"""
core/server.py
──────────────
FastAPI local IPC server + WebSocket stream.

Listens on localhost:8420. Provides:
  - REST endpoints for Tauri IPC (context injection, action callbacks)
  - WebSocket stream for real-time state updates to the UI
  - Startup lifecycle: initializes all context monitors and Nebius clients

This is the entry point for the Python daemon.
Run with: python core/server.py
"""

import asyncio
import os
import sys

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.capture.clipboard import ClipboardMonitor
from core.capture.ocr import OCRMonitor
from core.capture.process_watcher import ProcessWatcher
from core.capture.filesystem import FilesystemWatcher
from core.engine.aggregator import ContextAggregator, ContextBundle
from core.engine.state_machine import StateMachine, SynapseState
from core.nebius.client import NebiusClient
from core.nebius.router import NanoRouter
from core.nebius.memory import PGVectorMemory
from core.tools.tavily_search import TavilySearch

# ── App setup ─────────────────────────────────────────────────────────

app = FastAPI(
    title="Synapse Daemon",
    description="Local IPC server for the Synapse ambient AI layer",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global singletons ─────────────────────────────────────────────────

nebius: NebiusClient = None
memory: PGVectorMemory = None
router: NanoRouter = None
tavily: TavilySearch = None
aggregator: ContextAggregator = None
state_machine: StateMachine = None
_ws_connections: list[WebSocket] = []

# ── WebSocket broadcast ───────────────────────────────────────────────

async def broadcast(payload: dict) -> None:
    """Send a JSON payload to all connected UI WebSocket clients."""
    dead = []
    for ws in _ws_connections:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_connections.remove(ws)


# ── Startup: wire everything together ─────────────────────────────────

@app.on_event("startup")
async def startup() -> None:
    global nebius, memory, router, tavily, aggregator, state_machine

    print("[Synapse] Starting daemon on port 8420...")

    # Nebius clients
    nebius = NebiusClient()
    memory = PGVectorMemory(client=nebius)
    await memory.connect()
    await memory.bootstrap()
    router = NanoRouter(client=nebius)
    tavily = TavilySearch()

    # State machine
    state_machine = StateMachine(on_state_change=on_state_change)

    # Aggregator — main pipeline entry point
    aggregator = ContextAggregator(on_bundle=process_bundle)

    # Context monitors (background tasks)
    asyncio.create_task(start_capture_monitors())

    print("[Synapse] ✓ All systems online")


async def on_state_change(new_state: SynapseState) -> None:
    await broadcast({"type": "state_change", **state_machine.to_ui_payload()})


async def start_capture_monitors() -> None:
    """Start all slow-lane monitors as concurrent background tasks."""

    # OCR monitor — slow lane
    ocr_monitor = OCRMonitor(on_snapshot=aggregator.update_ocr)
    asyncio.create_task(ocr_monitor.start())

    # Process watcher — slow lane
    proc_watcher = ProcessWatcher(on_focus_change=aggregator.on_focus_change)
    asyncio.create_task(proc_watcher.start())

    # Filesystem watcher — slow lane
    fs_watcher = FilesystemWatcher(on_change=aggregator.update_project)
    await fs_watcher.start()

    # Clipboard monitor — fast lane (runs in a thread)
    clipboard = ClipboardMonitor(
        on_change=lambda event: asyncio.create_task(aggregator.on_clipboard_event(event))
    )
    clipboard.start()


# ── Core pipeline ─────────────────────────────────────────────────────

async def process_bundle(bundle: ContextBundle) -> None:
    """Main reasoning pipeline triggered by the aggregator."""
    await state_machine.transition(SynapseState.CAPTURING)

    # Retrieve relevant memories
    query_text = bundle.trigger_content or bundle.screen_text
    if query_text:
        memories = await memory.search(query_text[:500])
        bundle.memory_context = [
            {
                "problem_signature": m.problem_signature,
                "resolution_summary": m.resolution_summary,
                "similarity": m.similarity,
            }
            for m in memories
        ]

    await state_machine.transition(SynapseState.REASONING)

    # Route through Nano → Ultra
    output = await router.route(bundle)
    if not output:
        await state_machine.transition(SynapseState.IDLE)
        return

    # Tavily if needed
    tavily_data = None
    if output.requires_tavily and output.tavily_query:
        search_result = await tavily.search(output.tavily_query)
        tavily_data = {
            "query": search_result.query,
            "saved_path": search_result.saved_path,
            "sources": [{"title": r.title, "url": r.url} for r in search_result.results[:3]],
        }

    await state_machine.transition(SynapseState.READY)

    # Broadcast card payload to UI
    await broadcast({
        "type": "synapse_card",
        "trigger": bundle.trigger_source.name,
        "response": output.final_response,
        "model_used": output.model_used,
        "latency_ms": output.latency_ms,
        "active_app": bundle.active_app,
        "memory_used": len(bundle.memory_context) > 0,
        "tavily": tavily_data,
        "usage": nebius.usage_summary(),
    })


# ── REST endpoints ────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "state": state_machine.state_name if state_machine else "starting"}


@app.post("/invoke")
async def manual_invoke(body: dict):
    """Manual invocation endpoint — called when user presses Ctrl+Shift+Space."""
    query = body.get("query", "")
    if aggregator:
        await aggregator.on_manual_invoke(query)
    return {"status": "processing"}


@app.post("/action/apply-fix")
async def action_apply_fix(body: dict):
    """Called when user clicks 'Apply Fix' on the overlay card."""
    # TODO: Clipboard injection or editor bridge
    patch = body.get("patch", "")
    if patch:
        import win32clipboard, win32con
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(patch, win32con.CF_UNICODETEXT)
        win32clipboard.CloseClipboard()
    return {"status": "applied"}


@app.post("/action/store-memory")
async def action_store_memory(body: dict):
    """Called when user accepts a fix — stores it in PGVector memory."""
    if memory:
        await memory.store(
            application_context=body.get("app_context", "unknown"),
            problem_signature=body.get("problem", ""),
            resolution_summary=body.get("resolution", ""),
            file_extensions=body.get("extensions", []),
        )
    return {"status": "stored"}


@app.post("/action/dismiss")
async def action_dismiss():
    """Card dismissed by user — enter suppression cooldown."""
    if state_machine:
        await state_machine.transition(SynapseState.SUPPRESSED)
    return {"status": "suppressed"}


@app.get("/usage")
async def usage():
    """Return current Nebius credit usage estimate."""
    if nebius:
        return nebius.usage_summary()
    return {}


# ── WebSocket ─────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_connections.append(ws)
    try:
        while True:
            # Keep connection alive; UI sends pings
            data = await ws.receive_text()
            if data == "ping":
                await ws.send_text("pong")
    except WebSocketDisconnect:
        _ws_connections.remove(ws)


# ── Entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run(
        "core.server:app",
        host="127.0.0.1",
        port=8420,
        log_level="info",
        reload=False,
    )
