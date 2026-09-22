"""tests/test_nebius_routing.py — Nebius routing unit tests (mocked)."""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from core.nebius.router import NanoRouter, RoutingDecision
from core.engine.aggregator import ContextBundle, TriggerSource


def _make_bundle(trigger_content="ValueError: NoneType"):
    return ContextBundle(
        trigger_source=TriggerSource.CLIPBOARD_ERROR,
        trigger_content=trigger_content,
        trigger_score=95,
        active_app="Code",
        screen_text="def fetch(id):\n    return db.get(id).name",
    )


@pytest.mark.asyncio
async def test_router_nano_sufficient():
    """When Nano says nano_sufficient and score >= threshold, no Ultra call."""
    client = MagicMock()
    client.complete_nano = AsyncMock(return_value=json.dumps({
        "relevance_score": 80,
        "decision": "nano_sufficient",
        "needs_tavily": False,
        "tavily_query": None,
        "nano_response": "The error is because db.get() returns None.",
        "reasoning_hint": "",
    }))
    client.complete_ultra = AsyncMock()

    router = NanoRouter(client=client)
    bundle = _make_bundle()
    output = await router.route(bundle)

    assert output is not None
    assert output.decision == RoutingDecision.NANO_SUFFICIENT
    assert output.model_used == "nano"
    assert "None" in output.final_response
    client.complete_ultra.assert_not_called()


@pytest.mark.asyncio
async def test_router_escalates_to_ultra():
    """When Nano says escalate_ultra, Ultra must be called."""
    client = MagicMock()
    client.complete_nano = AsyncMock(return_value=json.dumps({
        "relevance_score": 90,
        "decision": "escalate_ultra",
        "needs_tavily": False,
        "tavily_query": None,
        "nano_response": None,
        "reasoning_hint": "Complex auth bug requiring cross-file analysis",
    }))
    client.complete_ultra = AsyncMock(return_value="The bug is in auth_service.py line 47...")

    router = NanoRouter(client=client)
    bundle = _make_bundle()
    output = await router.route(bundle)

    assert output is not None
    assert output.decision == RoutingDecision.ESCALATE_ULTRA
    assert output.model_used == "ultra"
    client.complete_ultra.assert_called_once()


@pytest.mark.asyncio
async def test_router_ignores_low_relevance():
    """When relevance_score < threshold, router should return None."""
    client = MagicMock()
    client.complete_nano = AsyncMock(return_value=json.dumps({
        "relevance_score": 20,
        "decision": "ignore",
        "needs_tavily": False,
        "tavily_query": None,
        "nano_response": None,
        "reasoning_hint": "",
    }))

    router = NanoRouter(client=client)
    bundle = _make_bundle("Meeting notes from yesterday")
    output = await router.route(bundle)
    assert output is None


def test_parse_triage_json_bare():
    raw = '{"relevance_score": 90, "decision": "escalate_ultra"}'
    parsed = NanoRouter._parse_triage_json(raw)
    assert parsed["decision"] == "escalate_ultra"


def test_parse_triage_json_fenced():
    raw = '```json\n{"relevance_score": 90, "decision": "escalate_ultra"}\n```'
    parsed = NanoRouter._parse_triage_json(raw)
    assert parsed["relevance_score"] == 90


def test_parse_triage_json_with_prose():
    raw = 'Here is my analysis:\n{"relevance_score": 10, "decision": "ignore"}\nHope this helps.'
    parsed = NanoRouter._parse_triage_json(raw)
    assert parsed["decision"] == "ignore"


def test_parse_triage_json_empty_and_garbage():
    assert NanoRouter._parse_triage_json("") is None
    assert NanoRouter._parse_triage_json("   ") is None
    assert NanoRouter._parse_triage_json("no json here at all") is None
    assert NanoRouter._parse_triage_json("[1, 2, 3]") is None


@pytest.mark.asyncio
async def test_router_empty_nano_response_ignores():
    """Empty Nano output (seen live with max_tokens=256) must not crash."""
    client = MagicMock()
    client.complete_nano = AsyncMock(return_value="")
    router = NanoRouter(client=client)
    output = await router.route(_make_bundle())
    assert output is None
