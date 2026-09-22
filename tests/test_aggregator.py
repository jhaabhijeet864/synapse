"""tests/test_aggregator.py — Context aggregator unit tests."""
import asyncio
import pytest
from core.capture.clipboard import ClipboardEvent, ClipboardContentType
from core.engine.aggregator import ContextAggregator, ContextBundle, TriggerSource


@pytest.mark.asyncio
async def test_error_clipboard_triggers_bundle():
    """Copying an error traceback should emit a bundle above threshold."""
    emitted: list[ContextBundle] = []

    async def capture(bundle): emitted.append(bundle)

    agg = ContextAggregator(on_bundle=capture)
    event = ClipboardEvent(
        content="Traceback (most recent call last):\n  File 'app.py'\nValueError: NoneType",
        content_type=ClipboardContentType.ERROR_TRACEBACK,
    )
    await agg.on_clipboard_event(event)
    assert len(emitted) == 1
    assert emitted[0].trigger_source == TriggerSource.CLIPBOARD_ERROR
    assert emitted[0].trigger_score >= 90


@pytest.mark.asyncio
async def test_plain_text_clipboard_does_not_trigger():
    """Plain text clipboard should NOT emit a bundle (score below threshold)."""
    emitted: list[ContextBundle] = []

    async def capture(bundle): emitted.append(bundle)

    agg = ContextAggregator(on_bundle=capture)
    event = ClipboardEvent(content="hello world", content_type=ClipboardContentType.PLAIN_TEXT)
    await agg.on_clipboard_event(event)
    assert len(emitted) == 0


@pytest.mark.asyncio
async def test_manual_invoke_always_triggers():
    """Manual invocation should always emit a bundle regardless of score."""
    emitted: list[ContextBundle] = []

    async def capture(bundle): emitted.append(bundle)

    agg = ContextAggregator(on_bundle=capture)
    await agg.on_manual_invoke("what is this error?")
    assert len(emitted) == 1
    assert emitted[0].trigger_source == TriggerSource.MANUAL_INVOKE


@pytest.mark.asyncio
async def test_suppression_prevents_double_trigger():
    """Two rapid triggers should only emit once due to suppression."""
    emitted: list[ContextBundle] = []

    async def capture(bundle): emitted.append(bundle)

    agg = ContextAggregator(on_bundle=capture)
    agg.SUPPRESSION_SECS = 60  # Ensure suppression is active

    event = ClipboardEvent(
        content="TypeError: cannot read properties of undefined",
        content_type=ClipboardContentType.ERROR_TRACEBACK,
    )
    await agg.on_clipboard_event(event)
    await agg.on_clipboard_event(event)  # Second trigger — should be suppressed
    assert len(emitted) == 1


def test_context_bundle_to_prompt():
    """ContextBundle should produce a non-empty prompt context string."""
    bundle = ContextBundle(
        trigger_source=TriggerSource.CLIPBOARD_ERROR,
        trigger_content="ValueError: NoneType is not subscriptable",
        trigger_score=95,
        active_app="Code",
        screen_text="def get_user(id):\n    return db.query(id).first()",
        focus_duration_mins=12.5,
    )
    prompt = bundle.to_prompt_context()
    assert "CLIPBOARD_ERROR" in prompt
    assert "Code" in prompt
    assert "ValueError" in prompt
