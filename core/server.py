"""
core/server.py
──────────────
FastAPI local IPC server + WebSocket stream.

Listens on localhost:8420. Provides:
  - REST endpoints for Tauri IPC (context injection, action callbacks)
  - WebSocket stream for real-time state updates to the UI
  - Startup lifecycle: initializes all context monitors and Nebius clients

This is the entry point for the Python daemon.
Run from repo root with either:
    python core/server.py
    python -m core.server
"""

import asyncio
import os
import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Allow `python core/server.py` from the repo root: running a file inside
# a package puts core/ (not the root) on sys.path, which breaks `from core…`
# imports. Insert the repo root when executed as a script.
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from core.capture.clipboard import ClipboardMonitor
from core.capture.ocr import OCRMonitor
from core.capture.process_watcher import ProcessWatcher
from core.capture.filesystem import FilesystemWatcher
from core.engine.aggregator import ContextAggregator, ContextBundle
from core.engine.state_machine import StateMachine, SynapseState
from core.logging_config import setup_logging
from core.nebius.client import NebiusClient
from core.nebius.router import NanoRouter, RoutingDecision
from core.nebius.memory import PGVectorMemory
from core.tools.file_patcher import FilePatcher
from core.tools.tavily_search import TavilySearch

# ── App setup ─────────────────────────────────────────────────────────

logger = setup_logging()

# Event loop of the async runtime, captured at startup. Win32 monitor
# threads (clipboard) must schedule coroutines via run_coroutine_threadsafe
# — asyncio.create_task() has no running loop on those threads.
_main_loop: asyncio.AbstractEventLoop | None = None


def _on_clipboard_threadsafe(event) -> None:
    """Thread-safe bridge: Win32 WNDPROC thread → async aggregator."""
    if _main_loop is None or aggregator is None:
        return
    try:
        asyncio.run_coroutine_threadsafe(aggregator.on_clipboard_event(event), _main_loop)
    except RuntimeError as e:
        logger.warning(f"clipboard bridge dropped event: {e}")


async def _startup() -> None:
    global nebius, memory, router, tavily, aggregator, state_machine, _main_loop

    print("[Synapse] Starting daemon on port 8420...")
    _main_loop = asyncio.get_running_loop()

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

    print("[Synapse] All systems online")


async def _shutdown() -> None:
    if memory:
        await memory.close()
    print("[Synapse] Daemon stopped")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _startup()
    yield
    await _shutdown()


app = FastAPI(
    title="Synapse Daemon",
    description="Local IPC server for the Synapse ambient AI layer",
    version="0.1.0",
    lifespan=lifespan,
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
# (lifespan handlers above; monitors below)

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

    # Clipboard monitor — fast lane (runs in a Win32 thread; bridge
    # schedules onto the captured loop — never create_task() here)
    clipboard = ClipboardMonitor(on_change=_on_clipboard_threadsafe)
    clipboard.start()


# ── Core pipeline ─────────────────────────────────────────────────────
# Order: memory → Nano triage → Tavily (if gap) → Ultra (streamed).
# Tavily results are injected into the Ultra prompt BEFORE reasoning,
# so the model actually uses live sources instead of just displaying them.

async def process_bundle(bundle: ContextBundle) -> None:
    """Main reasoning pipeline triggered by the aggregator."""
    t0 = time.perf_counter()
    await state_machine.transition(SynapseState.CAPTURING)

    # Retrieve relevant memories & log pgvector lookup
    query_text = bundle.trigger_content or bundle.screen_text
    tokens_triaged_local = 0
    if query_text:
        try:
            memories = await memory.search(query_text[:500])
        except Exception as e:
            print(json.dumps({"stage": "pgvector_lookup", "similarity": 0.0, "latency_ms": int((time.perf_counter() - t0) * 1000)}))
            memories = []
        bundle.memory_context = [
            {
                "problem_signature": m.problem_signature,
                "resolution_summary": m.resolution_summary,
                "similarity": m.similarity,
            }
            for m in memories
        ]
        # Token efficiency: tokens triaged locally by Nano vs total screen context
        tokens_triaged_local = len(query_text) // 4

    await state_machine.transition(SynapseState.REASONING)

    # Stage 1: Nano triage (cheap — decides everything downstream)
    try:
        triage = await router.triage(bundle)
    except Exception as e:
        print(f"[Pipeline] Triage failed: {e}")
        await state_machine.transition(SynapseState.IDLE)
        return
    if triage is None:
        await state_machine.transition(SynapseState.IDLE)
        return

    trigger_name = bundle.trigger_source.name
    latency_ms = lambda: round((time.perf_counter() - t0) * 1000, 1)

    # Compute credit efficiency: % of tokens handled by Nano vs full screen context
    total_screen_tokens = len(bundle.screen_text) // 4 if bundle.screen_text else 0
    efficiency_pct = round(tokens_triaged_local / max(total_screen_tokens, 1) * 100, 1) if total_screen_tokens else 0

    # Stage 2a: Nano-sufficient — answer directly, no Ultra spend
    if triage.decision == RoutingDecision.NANO_SUFFICIENT:
        await state_machine.transition(SynapseState.READY)
        await broadcast({
            "type": "synapse_card",
            "trigger": trigger_name,
            "response": triage.nano_response,
            "model_used": "nano",
            "latency_ms": latency_ms(),
            "active_app": bundle.active_app,
            "memory_used": len(bundle.memory_context) > 0,
            "tavily": None,
            "usage": nebius.usage_summary(),
        })
        # Log efficiency even on Nano-only path
        logger.info(
            {
                "stage": "efficiency",
                "tokens_triaged_local": tokens_triaged_local,
                "total_screen_tokens": total_screen_tokens,
                "efficiency_pct": efficiency_pct,
            }
        )
        return

    # Stage 2b: Tavily first (when Nano detects a knowledge gap)
    tavily_data = None
    tavily_injection = ""
    if triage.requires_tavily and triage.tavily_query:
        try:
            search_result = await tavily.search(triage.tavily_query)
            tavily_injection = search_result.to_prompt_injection()
            tavily_data = {
                "query": search_result.query,
                "saved_path": search_result.saved_path,
                "sources": [{"title": r.title, "url": r.url} for r in search_result.results[:3]],
            }
        except Exception as e:
            print(f"[Pipeline] Tavily search failed: {e}")

    # Stage 3: Ultra with memory + Tavily context, streamed to the UI
    ultra_prompt = router.build_ultra_prompt(bundle, triage, tavily_injection)
    parts: list[str] = []
    try:
        async for delta in nebius.complete_ultra_stream(ultra_prompt):
            parts.append(delta)
            await broadcast({"type": "synapse_chunk", "trigger": trigger_name, "delta": delta})
    except Exception as e:
        print(f"[Pipeline] Ultra stream failed: {e}")
        await state_machine.transition(SynapseState.IDLE)
        return

    await state_machine.transition(SynapseState.READY)

    # Broadcast card payload to UI
    logger.info(
        json.dumps({
            "stage": "efficiency",
            "tokens_triaged_local": tokens_triaged_local,
            "total_screen_tokens": total_screen_tokens,
            "efficiency_pct": efficiency_pct,
        })
    )
    await broadcast({
        "type": "synapse_card",
        "trigger": trigger_name,
        "response": "".join(parts),
        "model_used": "ultra",
        "latency_ms": latency_ms(),
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
    """Apply a unified diff to the active project, else copy patch to clipboard.

    Body: {"patch": "<unified diff>", "project_path": "<optional override>"}.
    FilePatcher guards path traversal + backs up (.bak) before writing.
    """
    patch = body.get("patch", "")
    if not patch:
        return {"status": "empty", "patched": []}

    project_root = body.get("project_path") or (
        aggregator.get_project_root() if aggregator else ""
    )
    patched: list[dict] = []
    if project_root:
        try:
            results = FilePatcher(project_root=project_root).apply(patch)
            patched = [
                {
                    "file": r.patched_file,
                    "success": r.success,
                    "backup": r.backup_path,
                    "lines_changed": r.lines_changed,
                    "error": r.error,
                }
                for r in results
            ]
        except Exception as e:
            print(f"[ApplyFix] FilePatcher failed: {e}")

    if not any(p["success"] for p in patched):
        # No parseable diff or patch failed — put it on the clipboard instead.
        try:
            import win32clipboard, win32con
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(patch, win32con.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
            return {"status": "clipboard", "patched": patched}
        except Exception as e:
            return {"status": "failed", "error": str(e), "patched": patched}
    return {"status": "applied", "patched": patched}


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
