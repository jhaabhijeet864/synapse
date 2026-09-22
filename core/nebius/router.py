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
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Optional

from core.engine.aggregator import ContextBundle
from core.engine.redaction import scrub
from core.nebius.client import NebiusClient

from core.logging_config import setup_logging

logger = setup_logging()


class RoutingDecision(Enum):
    NANO_SUFFICIENT  = auto()  # Nano can handle this alone
    ESCALATE_ULTRA   = auto()  # Needs Nemotron 3 Ultra
    NEEDS_TAVILY     = auto()  # Needs web search before Ultra
    IGNORE           = auto()  # Not relevant enough to surface


@dataclass
class TriageResult:
    """Stage-1 output: Nano's classification before any Ultra/Tavily work."""
    decision: RoutingDecision
    decision_str: str               # Raw string from Nano ("escalate_ultra", …)
    relevance: int                  # 0-100 relevance score
    requires_tavily: bool
    tavily_query: Optional[str]
    nano_response: str              # Set when decision == NANO_SUFFICIENT
    reasoning_hint: str
    safe_context: str               # Scrubbed bundle text (reused for Ultra prompt)


TAVILY_SECTION_TEMPLATE = """WEB RESEARCH (Tavily):
{tavily}
(Use these live sources. Prefer them over training-data knowledge.)"""


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

{tavily_section}

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

    async def triage(self, bundle: ContextBundle) -> Optional[TriageResult]:
        """
        Stage 1 only: scrub + Nano classification. Returns None when the
        bundle scores below RELEVANCE_THRESHOLD (not worth surfacing).
        """
        safe_context = scrub(bundle.to_prompt_context())
        triage_prompt = NANO_TRIAGE_PROMPT.format(context=safe_context)
        nano_raw = await self._client.complete_nano(triage_prompt, max_tokens=256)

        try:
            triage = json.loads(nano_raw.strip())
        except json.JSONDecodeError:
            # Nano returned malformed JSON — extract what we can
            triage = {"decision": "ignore", "relevance_score": 0}

        relevance = triage.get("relevance_score", 0)
        decision_str = triage.get("decision", "ignore")

        decision_map = {
            "nano_sufficient": RoutingDecision.NANO_SUFFICIENT,
            "escalate_ultra":  RoutingDecision.ESCALATE_ULTRA,
            "needs_tavily":    RoutingDecision.NEEDS_TAVILY,
            "ignore":          RoutingDecision.IGNORE,
        }
        decision = decision_map.get(decision_str, RoutingDecision.IGNORE)

        # Below threshold — not worth surfacing (escalations always pass)
        if relevance < self.RELEVANCE_THRESHOLD and decision != RoutingDecision.ESCALATE_ULTRA:
            return None

        return TriageResult(
            decision=decision,
            decision_str=decision_str,
            relevance=relevance,
            requires_tavily=triage.get("needs_tavily", False),
            tavily_query=triage.get("tavily_query"),
            nano_response=triage.get("nano_response", "") or "",
            reasoning_hint=triage.get("reasoning_hint", "") or "",
            safe_context=safe_context,
        )

    def build_ultra_prompt(
        self,
        bundle: ContextBundle,
        triage: TriageResult,
        tavily_injection: str = "",
    ) -> str:
        """Assemble the Ultra prompt: context + hint + memory + Tavily."""
        memory_section = self._format_memory(bundle.memory_context)
        tavily_section = (
            TAVILY_SECTION_TEMPLATE.format(tavily=tavily_injection)
            if tavily_injection
            else ""
        )
        return ULTRA_REASONING_PROMPT.format(
            context=triage.safe_context,
            hint=triage.reasoning_hint,
            memory_section=memory_section,
            tavily_section=tavily_section,
        )

    async def route(self, bundle: ContextBundle) -> Optional[RouterOutput]:
        """
        Main entry point. Returns RouterOutput or None if context is irrelevant.
Compat path: triage -> Nano direct answer or Ultra (no Tavily injection;
        the server pipeline uses triage()/build_ultra_prompt() for that).
        """
        t0 = time.perf_counter()

        triage = await self.triage(bundle)
        if triage is None:
            return None

        # ── Stage 2: Return Nano response if sufficient ───────────────
        if triage.decision == RoutingDecision.NANO_SUFFICIENT:
            elapsed = (time.perf_counter() - t0) * 1000
            logger.info(
            {
                "stage": "nano_triage",
                "latency_ms": round(elapsed, 1),
                "escalate": False,
                "classification": triage.decision_str,
            }
        )
            return RouterOutput(
                decision=triage.decision,
                nano_classification=triage.decision_str,
                requires_tavily=False,
                tavily_query=None,
                final_response=triage.nano_response,
                model_used="nano",
                latency_ms=round(elapsed, 1),
            )

        # ── Stage 3: Escalate to Ultra ────────────────────────────────
        ultra_t0 = time.perf_counter()
        ultra_prompt = self.build_ultra_prompt(bundle, triage)
        ultra_response = await self._client.complete_ultra(ultra_prompt)
        elapsed = (time.perf_counter() - t0) * 1000

        ultra_elapsed = (time.perf_counter() - ultra_t0) * 1000

        # Estimate tokens from response length for efficiency metric
        tokens_in = len(ultra_prompt) // 4
        tokens_out = len(ultra_response) // 4

        logger.info(
            {
                "stage": "nemotron_ultra",
                "latency_ms": round(ultra_elapsed, 1),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "escalate": True,
            }
        )

        return RouterOutput(
            decision=triage.decision,
            nano_classification=triage.decision_str,
            requires_tavily=triage.requires_tavily,
            tavily_query=triage.tavily_query,
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
