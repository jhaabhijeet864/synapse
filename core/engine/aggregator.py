"""
core/engine/aggregator.py
─────────────────────────
Layered Context Fusion Engine.

Merges the FAST LANE (clipboard, window switch) and SLOW LANE
(OCR, filesystem, process focus) into a single Context Bundle
that gets passed downstream to the Nano router.

The Trigger Evaluator scores each fast-lane event and decides
whether to emit a full Context Bundle to the reasoning pipeline.

Architecture role: CORE — the brain stem of the system.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional

from core.capture.clipboard import ClipboardEvent, ClipboardContentType
from core.capture.ocr import OCRSnapshot
from core.capture.process_watcher import FocusState
from core.capture.filesystem import ProjectContext

from core.logging_config import setup_logging

logger = setup_logging()


class TriggerSource(Enum):
    CLIPBOARD_ERROR   = auto()  # Copied error/traceback — very high signal
    CLIPBOARD_CODE    = auto()  # Copied code snippet — medium signal
    WINDOW_RETURN     = auto()  # Returned to app after > 30min — high signal
    STUCK_PATTERN     = auto()  # Rapid app switching — high signal
    MANUAL_INVOKE     = auto()  # Ctrl+Shift+Space — always triggers
    AUTO_OCR_ERROR    = auto()  # OCR detected error text — high signal
    CLIPBOARD_OTHER   = auto()  # Other clipboard — low signal (ignored)


# Trigger scores (0–100). Emit if score >= EMIT_THRESHOLD.
TRIGGER_SCORES: dict[TriggerSource, int] = {
    TriggerSource.CLIPBOARD_ERROR: 95,
    TriggerSource.AUTO_OCR_ERROR:  90,
    TriggerSource.STUCK_PATTERN:   80,
    TriggerSource.WINDOW_RETURN:   75,
    TriggerSource.CLIPBOARD_CODE:  60,
    TriggerSource.MANUAL_INVOKE:   100,
    TriggerSource.CLIPBOARD_OTHER: 10,
}

EMIT_THRESHOLD = 60  # Minimum score to fire a reasoning request


@dataclass
class ContextBundle:
    """
    The unified context object passed to the Nano router.
    Assembles all available signals at the moment of trigger.
    """
    # Trigger metadata
    trigger_source: TriggerSource
    trigger_content: str                # What caused the trigger
    trigger_score: int
    triggered_at: datetime = field(default_factory=datetime.utcnow)

    # Slow lane enrichment (latest available at trigger time)
    screen_text: str = ""               # Last OCR snapshot
    active_app: str = ""
    window_title: str = ""
    focus_duration_mins: float = 0.0
    switch_frequency_per_hour: float = 0.0
    is_deep_work: bool = False
    is_stuck: bool = False

    # Clipboard rolling buffer (last 5 items)
    clipboard_recent: list[str] = field(default_factory=list)

    # Project context
    project_path: str = ""
    project_language: str = ""
    recent_files: list[str] = field(default_factory=list)

    # Memory (injected by nebius/memory.py after retrieval)
    memory_context: list[dict] = field(default_factory=list)

    def to_prompt_context(self) -> str:
        """
        Renders a compact natural-language summary for injection into
        the Nemotron prompt. Stays under ~500 tokens.
        """
        lines = [
            f"[SYNAPSE CONTEXT — {self.triggered_at.strftime('%H:%M:%S')}]",
            f"Trigger: {self.trigger_source.name} (score={self.trigger_score})",
            f"Active app: {self.active_app} | Focus: {self.focus_duration_mins:.1f} min",
            f"Is stuck: {self.is_stuck} | Deep work: {self.is_deep_work}",
        ]
        if self.project_path:
            lines.append(f"Project: {self.project_path} ({self.project_language})")
        if self.recent_files:
            lines.append(f"Recent files: {', '.join(self.recent_files[:3])}")
        if self.trigger_content:
            lines.append(f"\n[TRIGGER CONTENT]\n{self.trigger_content[:800]}")
        if self.screen_text:
            lines.append(f"\n[SCREEN TEXT (truncated)]\n{self.screen_text[:600]}")
        if self.clipboard_recent:
            lines.append(f"\n[RECENT CLIPBOARD]\n{chr(10).join(self.clipboard_recent[:3])}")
        if self.memory_context:
            lines.append("\n[PAST MEMORY]")
            for m in self.memory_context[:2]:
                lines.append(f"  - {m.get('problem_signature', '')[:100]}")
                lines.append(f"    → {m.get('resolution_summary', '')[:100]}")
        return "\n".join(lines)


class ContextAggregator:
    """
    Subscribes to all context sources via callbacks.
    Maintains the latest slow-lane state at all times.
    On fast-lane trigger, assembles a ContextBundle and emits to the pipeline.

    Usage:
        aggregator = ContextAggregator(on_bundle=reasoning_pipeline.process)
        # Wire up sources:
        aggregator.update_focus(focus_state)
        aggregator.on_clipboard_event(clipboard_event)   # fast lane
        aggregator.update_ocr(ocr_snapshot)
        aggregator.update_project(project_context)
    """

    # Suppression: don't fire again within this many seconds of last emit
    SUPPRESSION_SECS = 60

    def __init__(self, on_bundle):
        self.on_bundle = on_bundle

        # Slow-lane state cache (always fresh)
        self._focus_state: Optional[FocusState] = None
        self._ocr_snapshot: Optional[OCRSnapshot] = None
        self._project: Optional[ProjectContext] = None
        self._clipboard_history: list[str] = []

        self._last_emit_at: Optional[datetime] = None
        self._lock = asyncio.Lock()

    # ──────────────────────────────────────────────────────────────────
    # Slow-lane updates (no trigger evaluation, just state update)
    # ──────────────────────────────────────────────────────────────────

    def update_focus(self, state: FocusState) -> None:
        self._focus_state = state

    def update_ocr(self, snapshot: OCRSnapshot) -> None:
        self._ocr_snapshot = snapshot
        # OCR can auto-trigger if it detects an error pattern
        if self._ocr_contains_error(snapshot.text):
            asyncio.create_task(
                self._evaluate_and_emit(TriggerSource.AUTO_OCR_ERROR, snapshot.text)
            )

    def update_project(self, project: ProjectContext) -> None:
        self._project = project

    def get_project_root(self) -> str:
        """Active project root for scoped file operations ('' when unknown)."""
        return self._project.root_path if self._project else ""

    # ──────────────────────────────────────────────────────────────────
    # Fast-lane triggers
    # ──────────────────────────────────────────────────────────────────

    async def on_clipboard_event(self, event: ClipboardEvent) -> None:
        source = self._clipboard_type_to_trigger(event.content_type)
        self._clipboard_history.insert(0, event.content)
        self._clipboard_history = self._clipboard_history[:5]
        await self._evaluate_and_emit(source, event.content)

    async def on_manual_invoke(self, query: str = "") -> None:
        await self._evaluate_and_emit(TriggerSource.MANUAL_INVOKE, query, force=True)

    async def on_focus_change(self, event, state: FocusState) -> None:
        self._focus_state = state
        if state.is_stuck:
            await self._evaluate_and_emit(TriggerSource.STUCK_PATTERN, f"Stuck: rapid switching between {state.recent_apps}")
        # Window return (came back after long absence — detect via history)
        # TODO: Track last-seen timestamps per app

    # ──────────────────────────────────────────────────────────────────
    # Trigger evaluation
    # ──────────────────────────────────────────────────────────────────

    async def _evaluate_and_emit(self, source: TriggerSource, content: str, force: bool = False) -> None:
        score = TRIGGER_SCORES.get(source, 0)
        if score < EMIT_THRESHOLD and not force:
            return

        async with self._lock:
            # Suppression check
            if not force and self._last_emit_at:
                elapsed = (datetime.utcnow() - self._last_emit_at).total_seconds()
                if elapsed < self.SUPPRESSION_SECS:
                    return

            bundle = self._build_bundle(source, content, score)
            self._last_emit_at = datetime.utcnow()

        await self.on_bundle(bundle)

    def _build_bundle(self, source: TriggerSource, content: str, score: int) -> ContextBundle:
        fs = self._focus_state
        ocr = self._ocr_snapshot
        proj = self._project
        return ContextBundle(
            trigger_source=source,
            trigger_content=content,
            trigger_score=score,
            screen_text=ocr.text if ocr else "",
            active_app=fs.active_app if fs else "",
            window_title=fs.window_title if fs else "",
            focus_duration_mins=fs.focus_duration_mins if fs else 0,
            switch_frequency_per_hour=fs.switch_frequency_per_hour if fs else 0,
            is_deep_work=fs.is_deep_work if fs else False,
            is_stuck=fs.is_stuck if fs else False,
            clipboard_recent=list(self._clipboard_history),
            project_path=proj.root_path if proj else "",
            project_language=proj.language if proj else "",
            recent_files=proj.recent_files[:5] if proj else [],
        )

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _clipboard_type_to_trigger(ct: ClipboardContentType) -> TriggerSource:
        mapping = {
            ClipboardContentType.ERROR_TRACEBACK: TriggerSource.CLIPBOARD_ERROR,
            ClipboardContentType.CODE_SNIPPET:    TriggerSource.CLIPBOARD_CODE,
        }
        return mapping.get(ct, TriggerSource.CLIPBOARD_OTHER)

    @staticmethod
    def _ocr_contains_error(text: str) -> bool:
        error_patterns = [
            "traceback", "error:", "exception:", "failed:", "fatal:",
            "cannot find", "undefined", "null reference", "segmentation fault",
        ]
        lowered = text.lower()
        return any(p in lowered for p in error_patterns)
