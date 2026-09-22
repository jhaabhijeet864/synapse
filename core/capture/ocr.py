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
import win32process
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
        if self._paddle_ocr is not None:
            return
        from paddleocr import PaddleOCR
        # use_angle_cls=False for speed; det=True, rec=True are defaults
        loop = asyncio.get_event_loop()
        self._paddle_ocr = await loop.run_in_executor(
            None, lambda: PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
        )

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
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        app_name = self._get_process_name(pid)

        # Capture window bitmap
        try:
            image = self._capture_window_bitmap(hwnd)
        except Exception as e:
            print(f"[OCR] Bitmap capture failed: {e}")
            return None

        # Run OCR — prefer WinRT, auto-fallback to PaddleOCR on any failure
        # so one broken lane never kills ambient capture.
        try:
            if self._use_winrt:
                try:
                    text = await self._winrt_ocr(image)
                except Exception as e:
                    print(f"[OCR] WinRT failed ({e}), trying PaddleOCR fallback")
                    if self._paddle_ocr is None:
                        await self._init_paddleocr()
                    text = await self._paddleocr_extract(image)
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
        """Run WinRT OCR on a PIL Image via SoftwareBitmap pipeline.

        Pipeline: PIL RGB -> PNG bytes -> InMemoryRandomAccessStream ->
        BitmapDecoder -> SoftwareBitmap (Gray8) -> OcrEngine.recognize_async.

        Runs natively async (no executor — WinRT COM needs the calling
        thread). Raises on failure so the caller can fall back to PaddleOCR.
        """
        import asyncio
        import io

        if self._engine is None:
            raise RuntimeError("WinRT OCR engine not initialized")

        import winrt.windows.graphics.imaging as imaging
        import winrt.windows.storage.streams as streams

        # Normalize: WinRT OCR wants Gray8 or Bgra8. Encode as PNG bytes.
        rgb = image.convert("RGB")
        buf = io.BytesIO()
        # Downscale very large captures to bound latency/memory (< 2200px max dim)
        max_dim = 2200
        if max(rgb.size) > max_dim:
            rgb.thumbnail((max_dim, max_dim), Image.LANCZOS)
        rgb.save(buf, format="PNG")
        raw = buf.getvalue()

        # Bytes -> WinRT random-access stream
        mem_stream = streams.InMemoryRandomAccessStream()
        writer = streams.DataWriter(mem_stream.get_output_stream_at(0))
        writer.write_bytes(raw)
        await writer.store_async()
        await writer.flush_async()
        writer.detach_stream()
        mem_stream.seek(0)

        # Decode -> SoftwareBitmap
        decoder = await imaging.BitmapDecoder.create_async(mem_stream)
        software_bitmap = await decoder.get_software_bitmap_async()

        # Convert to Gray8 (most compatible for OcrEngine across Win builds)
        if software_bitmap.bitmap_pixel_format != imaging.BitmapPixelFormat.GRAY8:
            software_bitmap = imaging.SoftwareBitmap.convert(
                software_bitmap, imaging.BitmapPixelFormat.GRAY8
            )

        # Recognize with a safety timeout so a hung COM call can't stall the lane
        result = await asyncio.wait_for(
            self._engine.recognize_async(software_bitmap), timeout=15.0
        )
        return (result.text or "").strip()

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

    def __init__(self, on_snapshot, poll_interval: float | None = None):
        self.on_snapshot = on_snapshot
        # Default from Settings (env SYNAPSE_OCR_POLL_INTERVAL) unless overridden.
        if poll_interval is None:
            try:
                from core.config import settings
                poll_interval = settings.ocr_poll_interval_s
            except Exception:
                poll_interval = WindowsOCR.POLL_INTERVAL_S
        self.poll_interval = poll_interval
        self._ocr = WindowsOCR()
        self._running = False

    async def start(self) -> None:
        await self._ocr.initialize()
        self._running = True
        while self._running:
            try:
                snapshot = await self._ocr.capture_active_window()
            except Exception as e:
                print(f"[OCR] Monitor poll failed: {e}")
                snapshot = None
            if snapshot:
                try:
                    result = self.on_snapshot(snapshot)
                    # Support both sync callbacks (aggregator.update_ocr) and async ones
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    print(f"[OCR] on_snapshot handler failed: {e}")
            await asyncio.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
