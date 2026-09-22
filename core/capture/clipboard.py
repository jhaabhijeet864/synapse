"""
core/capture/clipboard.py
─────────────────────────
Sub-millisecond Win32 clipboard listener.

Uses a Win32 message-only window to receive WM_CLIPBOARDUPDATE notifications
without polling. Emits events to the internal asyncio event bus immediately
on change. Raw content never leaves this module without going through the
redactor first.

Architecture role: FAST LANE — triggers < 10ms after clipboard change.
"""

import asyncio
import ctypes
import ctypes.wintypes
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Callable, Optional

import win32api
import win32clipboard
import win32con
import win32gui


class ClipboardContentType(Enum):
    ERROR_TRACEBACK = auto()   # Python/JS/C# stack trace
    CODE_SNIPPET    = auto()   # Likely source code
    URL             = auto()   # HTTP/HTTPS link
    FILE_PATH       = auto()   # Absolute or relative path
    PLAIN_TEXT      = auto()   # Generic text
    BINARY          = auto()   # Non-text format — ignored


@dataclass
class ClipboardEvent:
    content: str
    content_type: ClipboardContentType
    timestamp: datetime = field(default_factory=datetime.utcnow)
    char_count: int = 0

    def __post_init__(self):
        self.char_count = len(self.content)


class ClipboardMonitor:
    """
    Registers a hidden Win32 message window and listens for
    WM_CLIPBOARDUPDATE. Calls `on_change` callback with a ClipboardEvent
    on every meaningful clipboard change.

    Usage:
        monitor = ClipboardMonitor(on_change=my_handler)
        monitor.start()
        ...
        monitor.stop()
    """

    MAX_HISTORY = 10          # Rolling buffer size
    MIN_CONTENT_LENGTH = 3    # Ignore single chars / trivial copies
    MAX_CONTENT_LENGTH = 50_000  # Skip huge binary pastes

    def __init__(self, on_change: Callable[[ClipboardEvent], None]):
        self.on_change = on_change
        self._history: list[ClipboardEvent] = []
        self._thread: Optional[threading.Thread] = None
        self._hwnd: Optional[int] = None
        self._running = False

    # ──────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the listener thread. Non-blocking."""
        self._running = True
        self._thread = threading.Thread(target=self._message_loop, daemon=True, name="ClipboardMonitor")
        self._thread.start()

    def stop(self) -> None:
        """Stop the listener and destroy the hidden window."""
        self._running = False
        if self._hwnd:
            win32gui.PostMessage(self._hwnd, win32con.WM_DESTROY, 0, 0)

    @property
    def history(self) -> list[ClipboardEvent]:
        """Returns the last N clipboard events (most recent first)."""
        return list(reversed(self._history))

    # ──────────────────────────────────────────────────────────────────
    # Internal — Win32 message loop
    # ──────────────────────────────────────────────────────────────────

    def _message_loop(self) -> None:
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self._wnd_proc
        wc.lpszClassName = "SynapseClipboardWatcher"
        wc.hInstance = win32api.GetModuleHandle(None)
        win32gui.RegisterClass(wc)

        self._hwnd = win32gui.CreateWindow(
            wc.lpszClassName, "Synapse Clipboard Watcher",
            0, 0, 0, 0, 0,
            win32con.HWND_MESSAGE, 0, wc.hInstance, None
        )
        ctypes.windll.user32.AddClipboardFormatListener(self._hwnd)
        win32gui.PumpMessages()

    # WM_CLIPBOARDUPDATE (0x031D) is NOT in pywin32's win32con —
    # referencing win32con.WM_CLIPBOARDUPDATE raises AttributeError and
    # kills the fast-lane listener on the first clipboard change.
    WM_CLIPBOARDUPDATE = 0x031D

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == self.WM_CLIPBOARDUPDATE:
            self._handle_change()
        elif msg == win32con.WM_DESTROY:
            ctypes.windll.user32.RemoveClipboardFormatListener(hwnd)
            win32gui.PostQuitMessage(0)
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _handle_change(self) -> None:
        try:
            win32clipboard.OpenClipboard(self._hwnd)
            try:
                if not win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                    return
                raw = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            return

        if not isinstance(raw, str):
            return
        content = raw.strip()
        if len(content) < self.MIN_CONTENT_LENGTH or len(content) > self.MAX_CONTENT_LENGTH:
            return

        event = ClipboardEvent(
            content=content,
            content_type=self._classify(content),
        )
        self._history.append(event)
        if len(self._history) > self.MAX_HISTORY:
            self._history.pop(0)

        self.on_change(event)

    # ──────────────────────────────────────────────────────────────────
    # Content classification (heuristic — fast, no LLM needed)
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _classify(text: str) -> ClipboardContentType:
        lowered = text.lower()

        # Error traceback patterns
        traceback_signals = ["traceback", "error:", "exception:", "at line", "syntaxerror",
                             "typeerror", "valueerror", "nameerror", "runtimeerror",
                             "nullpointerexception", "cannot find module", "segmentation fault"]
        if any(sig in lowered for sig in traceback_signals):
            return ClipboardContentType.ERROR_TRACEBACK

        # URL
        if text.startswith(("http://", "https://", "www.")):
            return ClipboardContentType.URL

        # File path
        if any(text.startswith(p) for p in ("C:\\", "D:\\", "E:\\", "/home/", "/usr/", "./")):
            return ClipboardContentType.FILE_PATH

        # Code heuristic — contains common code tokens
        code_signals = ["def ", "class ", "import ", "const ", "function ", "=>", "::"]
        if any(sig in text for sig in code_signals):
            return ClipboardContentType.CODE_SNIPPET

        return ClipboardContentType.PLAIN_TEXT
