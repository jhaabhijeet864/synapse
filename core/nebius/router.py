"""
core/nebius/router.py
─────────────────────
Tiered routing: Nemotron Nano (triage) → Nemotron 3 Ultra (deep reasoning).

The router receives a ContextBundle, sends it to Nano for fast classification,
then decides whether to escalate to Ultra or return the Nano response directly.

Nano is used for:
  - Relevance scoring ("is this context worth reasoning about?")
  - Tool selection ("does this need Tavily search?")
  - Simple factual questions and short answers

Ultra is used for:
  - Code debugging with diff generation
  - Multi-file analysis
  - Synthesis of Tavily search results
  - Complex architectural questions

Target latencies:
  - Nano path: < 300ms end-to-end
  - Ultra path: < 4s end-to-end (with streaming for progressive display)
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional

from core.engine.aggregator import ContextBundle
from core.engine.redaction import scrub
from core.nebius.client import NebiusClient


class RoutingDecision(Enum):
    NANO_SUFFICIENT  = auto()  # Nano can handle this alone
    ESCALATE_ULTRA   = auto()  # Needs Nemotron 3 Ultra
    NEEDS_TAVILY     = auto()  # Needs web search before Ultra
    IGNORE           = auto()  # Not relevant enough to surface


@dataclass
class RouterOutput:
    decision: RoutingDecision
    nano_classification: str          # Nano's brief assessment
    requires_tavily: bool
    tavily_query: Optional[str]       # Query to send to Tavily if needed
    final_response: str               # The actual response shown to user
    model_used: str                   # "nano" | "ultra"
    latency_ms: float
    triggered_at: datetime = field(default_factory=datetime.utcnow)


# ── Prompt templates ──────────────────────────────────────────────────

NANO_TRIAGE_PROMPT = """You are Synapse's triage engine. Analyze the developer context below and respond in JSON only.

CONTEXT:
{context}

Respond with EXACTLY this JSON schema (no other text):
{{
  "relevance_score": <0-100, how relevant is this for developer assistance>,
  "decision": <"nano_sufficient" | "escalate_ultra" | "needs_tavily" | "ignore">,
  "needs_tavily": <true | false>,
  "tavily_query": <search query string if needs_tavily else null>,
  "nano_response": <short direct answer if nano_sufficient else null>,
  "reasoning_hint": <one sentence describing what Ultra should focus on>
}}"""

ULTRA_REASONING_PROMPT = """You are Synapse, an expert developer assistant with full context of what the user is working on.

CONTEXT BUNDLE:
{context}

TRIAGE HINT: {hint}

{memory_section}

Provide a precise, actionable response. If the issue involves code:
1. Explain the root cause in 2-3 sentences
2. Provide a unified diff patch (```diff format)
3. Add one sentence on how to prevent this in future

Keep response under 400 words. Be direct — no preamble."""

MEMORY_SECTION_TEMPLATE = """RELEVANT PAST SESSIONS:
{memories}
(Use these as context. If a similar problem was solved before, reference the previous solution.)"""


class NanoRouter:
    """
    Two-stage reasoning pipeline:
      1. Nano triage — fast classification, routing decision
      2. Ultra reasoning — invoked only when warranted

    Usage:
        router = NanoRouter(client=nebius_client)
        output = await router.route(context_bundle)
    """

    RELEVANCE_THRESHOLD = 55  # Ignore context bundles scoring below this

    def __init__(self, client: NebiusClient):
        self._client = client

    async def route(self, bundle: ContextBundle) -> Optional[RouterOutput]:
        """
        Main entry point. Returns RouterOutput or None if context is irrelevant.
        """
        import time
        t0 = time.perf_counter()

        # Scrub before sending to cloud
        safe_context = scrub(bundle.to_prompt_context())

        # ── Stage 1: Nano triage ──────────────────────────────────────
        triage_prompt = NANO_TRIAGE_PROMPT.format(context=safe_context)
        nano_raw = await self._client.complete_nano(triage_prompt, max_tokens=256)

        try:
            triage = json.loads(nano_raw.strip())
        except json.JSONDecodeError:
            # Nano returned malformed JSON — extract what we can
            triage = {"decision": "ignore", "relevance_score": 0}

        relevance = triage.get("relevance_score", 0)
        decision_str = triage.get("decision", "ignore")

        # Map string decision to enum
        decision_map = {
            "nano_sufficient": RoutingDecision.NANO_SUFFICIENT,
            "escalate_ultra":  RoutingDecision.ESCALATE_ULTRA,
            "needs_tavily":    RoutingDecision.NEEDS_TAVILY,
            "ignore":          RoutingDecision.IGNORE,
        }
        decision = decision_map.get(decision_str, RoutingDecision.IGNORE)

        # Below threshold — not worth surfacing
        if relevance < self.RELEVANCE_THRESHOLD and decision != RoutingDecision.ESCALATE_ULTRA:
            return None

        requires_tavily = triage.get("needs_tavily", False)
        tavily_query = triage.get("tavily_query")
        hint = triage.get("reasoning_hint", "")

        # ── Stage 2: Return Nano response if sufficient ───────────────
        if decision == RoutingDecision.NANO_SUFFICIENT:
            nano_response = triage.get("nano_response", "")
            elapsed = (time.perf_counter() - t0) * 1000
            return RouterOutput(
                decision=decision,
                nano_classification=decision_str,
                requires_tavily=False,
                tavily_query=None,
                final_response=nano_response,
                model_used="nano",
                latency_ms=round(elapsed, 1),
            )

        # ── Stage 3: Escalate to Ultra ────────────────────────────────
        memory_section = self._format_memory(bundle.memory_context)
        ultra_prompt = ULTRA_REASONING_PROMPT.format(
            context=safe_context,
            hint=hint,
            memory_section=memory_section,
        )
        ultra_response = await self._client.complete_ultra(ultra_prompt)
        elapsed = (time.perf_counter() - t0) * 1000

        return RouterOutput(
            decision=decision,
            nano_classification=decision_str,
            requires_tavily=requires_tavily,
            tavily_query=tavily_query,
            final_response=ultra_response,
            model_used="ultra",
            latency_ms=round(elapsed, 1),
        )

    @staticmethod
    def _format_memory(memories: list[dict]) -> str:
        if not memories:
            return ""
        mem_lines = []
        for m in memories[:2]:
            mem_lines.append(f"• Problem: {m.get('problem_signature', '')[:120]}")
            mem_lines.append(f"  Solution: {m.get('resolution_summary', '')[:120]}")
        return MEMORY_SECTION_TEMPLATE.format(memories="\n".join(mem_lines))
