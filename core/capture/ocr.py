"""
core/capture/ocr.py
───────────────────
Active window text extraction using Windows.Media.Ocr (WinRT).

Target: < 50ms per capture on an RTX 2050.
Runs in the SLOW LANE — captures every 5s, diffs against last snapshot
to avoid re-processing identical frames. Only processes changed regions.

Architecture role: SLOW LANE — async background enrichment.
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import win32gui
import win32ui
import win32con
import win32api
from PIL import Image
import ctypes


@dataclass
class OCRSnapshot:
    text: str
    window_title: str
    app_name: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    capture_ms: float = 0.0
    text_hash: str = ""

    def __post_init__(self):
        self.text_hash = hashlib.md5(self.text.encode()).hexdigest()

    def is_different_from(self, other: Optional["OCRSnapshot"]) -> bool:
        if other is None:
            return True
        return self.text_hash != other.text_hash


class WindowsOCR:
    """
    Captures the active window as a bitmap and extracts text using
    Windows.Media.Ocr.OcrEngine (WinRT) via the `winrt` Python bindings.

    Falls back to PaddleOCR if WinRT is unavailable.

    Usage:
        ocr = WindowsOCR()
        await ocr.initialize()
        snapshot = await ocr.capture_active_window()
    """

    POLL_INTERVAL_S = 5.0

    def __init__(self):
        self._engine = None
        self._last_snapshot: Optional[OCRSnapshot] = None
        self._use_winrt = True
        self._paddle_ocr = None

    async def initialize(self) -> None:
        """Initialize OCR engine. Prefers WinRT, falls back to PaddleOCR."""
        try:
            # WinRT OCR — fastest, no GPU required for basic capture
            import winrt.windows.media.ocr as winrt_ocr
            import winrt.windows.globalization as glob
            lang = glob.Language("en-US")
            self._engine = winrt_ocr.OcrEngine.try_create_from_language(lang)
            if self._engine is None:
                raise RuntimeError("WinRT OCR engine unavailable")
        except Exception as e:
            print(f"[OCR] WinRT unavailable ({e}), falling back to PaddleOCR")
            self._use_winrt = False
            await self._init_paddleocr()

    async def _init_paddleocr(self) -> None:
        """Lazy-load PaddleOCR to avoid slow import on startup."""
        from paddleocr import PaddleOCR
        # use_angle_cls=False for speed; det=True, rec=True are defaults
        self._paddle_ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)

    async def capture_active_window(self) -> Optional[OCRSnapshot]:
        """
        Capture and OCR the active window.
        Returns None if content is unchanged since last capture.
        """
        t0 = time.perf_counter()
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        window_title = win32gui.GetWindowText(hwnd)
        _, pid = win32gui.GetWindowThreadProcessId(hwnd)
        app_name = self._get_process_name(pid)

        # Capture window bitmap
        try:
            image = self._capture_window_bitmap(hwnd)
        except Exception as e:
            print(f"[OCR] Bitmap capture failed: {e}")
            return None

        # Run OCR
        try:
            if self._use_winrt:
                text = await self._winrt_ocr(image)
            else:
                text = await self._paddleocr_extract(image)
        except Exception as e:
            print(f"[OCR] Text extraction failed: {e}")
            return None

        if not text.strip():
            return None

        elapsed_ms = (time.perf_counter() - t0) * 1000
        snapshot = OCRSnapshot(
            text=text,
            window_title=window_title,
            app_name=app_name,
            capture_ms=round(elapsed_ms, 2),
        )

        # Diff check — skip if unchanged
        if not snapshot.is_different_from(self._last_snapshot):
            return None

        self._last_snapshot = snapshot
        return snapshot

    def get_last_snapshot(self) -> Optional[OCRSnapshot]:
        return self._last_snapshot

    # ──────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────

    def _capture_window_bitmap(self, hwnd: int) -> Image.Image:
        """Capture window client area as PIL Image."""
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top

        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        # Use PrintWindow for better compatibility with hardware-accelerated apps
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        image = Image.frombuffer("RGB", (bmpinfo["bmWidth"], bmpinfo["bmHeight"]), bmpstr, "raw", "BGRX", 0, 1)

        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return image

    async def _winrt_ocr(self, image: Image.Image) -> str:
        """Run WinRT OCR on a PIL Image. Runs in executor to avoid blocking."""
        import winrt.windows.media.ocr as winrt_ocr
        import winrt.windows.graphics.imaging as imaging
        import io

        loop = asyncio.get_event_loop()

        def _sync_ocr():
            # Convert PIL to SoftwareBitmap (simplified via buffer)
            buf = io.BytesIO()
            image.save(buf, format="BMP")
            # TODO: Full WinRT SoftwareBitmap conversion
            # Placeholder — integrate winrt.windows.graphics.imaging properly
            return ""

        return await loop.run_in_executor(None, _sync_ocr)

    async def _paddleocr_extract(self, image: Image.Image) -> str:
        """Run PaddleOCR on a PIL Image."""
        import numpy as np
        loop = asyncio.get_event_loop()
        img_array = np.array(image)

        def _sync():
            result = self._paddle_ocr.ocr(img_array, cls=False)
            if not result or not result[0]:
                return ""
            return "\n".join([line[1][0] for line in result[0] if line and line[1]])

        return await loop.run_in_executor(None, _sync)

    @staticmethod
    def _get_process_name(pid: int) -> str:
        """Get process name from PID."""
        try:
            import psutil
            return psutil.Process(pid).name()
        except Exception:
            return "unknown"


class OCRMonitor:
    """
    Continuously polls the active window every POLL_INTERVAL_S seconds.
    Emits OCRSnapshot events when content changes.
    """

    def __init__(self, on_snapshot, poll_interval: float = WindowsOCR.POLL_INTERVAL_S):
        self.on_snapshot = on_snapshot
        self.poll_interval = poll_interval
        self._ocr = WindowsOCR()
        self._running = False

    async def start(self) -> None:
        await self._ocr.initialize()
        self._running = True
        while self._running:
            snapshot = await self._ocr.capture_active_window()
            if snapshot:
                await self.on_snapshot(snapshot)
            await asyncio.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
