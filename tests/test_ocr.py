"""tests/test_ocr.py — OCR capture unit tests."""
import pytest
from core.capture.ocr import OCRSnapshot
from core.capture.clipboard import ClipboardMonitor, ClipboardContentType


def test_ocr_snapshot_diff_detection():
    """Identical text should return is_different_from=False."""
    a = OCRSnapshot(text="hello world", window_title="VS Code", app_name="Code")
    b = OCRSnapshot(text="hello world", window_title="VS Code", app_name="Code")
    assert not a.is_different_from(b)


def test_ocr_snapshot_detects_change():
    """Different text should return is_different_from=True."""
    a = OCRSnapshot(text="hello world", window_title="VS Code", app_name="Code")
    b = OCRSnapshot(text="TypeError: something failed", window_title="VS Code", app_name="Code")
    assert a.is_different_from(b)


def test_ocr_snapshot_none_baseline():
    """Any snapshot is different from None (no previous)."""
    snap = OCRSnapshot(text="some text", window_title="Notepad", app_name="notepad")
    assert snap.is_different_from(None)


def test_clipboard_classify_error():
    text = "Traceback (most recent call last):\n  ValueError: NoneType"
    result = ClipboardMonitor._classify(text)
    assert result == ClipboardContentType.ERROR_TRACEBACK


def test_clipboard_classify_url():
    result = ClipboardMonitor._classify("https://github.com/issues/123")
    assert result == ClipboardContentType.URL


def test_clipboard_classify_code():
    result = ClipboardMonitor._classify("def my_function(x):\n    return x + 1")
    assert result == ClipboardContentType.CODE_SNIPPET


def test_clipboard_classify_plain():
    result = ClipboardMonitor._classify("Meeting at 3pm tomorrow")
    assert result == ClipboardContentType.PLAIN_TEXT
