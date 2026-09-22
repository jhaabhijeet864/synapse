"""
core/nebius/client.py
─────────────────────
Nebius Token Factory & Serverless SDK wrapper.

Centralizes all Nebius API interactions:
  - Nemotron Nano & Ultra inference via OpenAI-compatible endpoint
  - Nebius Embeddings API for PGVector context encoding
  - Credit usage tracking and budget warnings

All API keys loaded from environment / Windows Credential Manager.
Never hardcoded.
"""

import os
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

import httpx
from openai import AsyncOpenAI  # Nebius uses OpenAI-compatible API


# ── Nebius endpoint configuration ─────────────────────────────────────

NEBIUS_BASE_URL = "https://api.studio.nebius.ai/v1"

MODELS = {
    "nano":       "Qwen/Qwen3-8B",          # Fast triage (~150ms)
    "ultra":      "nvidia/Llama-3.1-Nemotron-70B-Instruct",  # Deep reasoning
    "embed":      "BAAI/bge-en-icl",         # Embedding model for PGVector
}


@dataclass
class UsageRecord:
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    timestamp: float = field(default_factory=time.time)

    @property
    def estimated_cost_usd(self) -> float:
        """Rough cost estimate. Update with actual Nebius pricing."""
        rates = {"nano": 0.000002, "ultra": 0.000008, "embed": 0.0000001}
        rate = rates.get(self.model, 0.000005)
        return self.total_tokens * rate


class NebiusClient:
    """
    Async client for all Nebius cloud services used by Synapse.

    Wraps the OpenAI-compatible Nebius endpoint with:
    - Automatic retries (3x with exponential backoff)
    - Usage tracking across all requests
    - Budget alerting when credits run low
    - Streaming support for responsive UI

    Usage:
        client = NebiusClient()
        response = await client.complete_nano("classify this error: ...")
        response = await client.complete_ultra("generate a fix for: ...")
        embedding = await client.embed("error text here")
    """

    MAX_RETRIES = 3
    BUDGET_WARNING_USD = 5.0     # Warn when estimated spend > $45 of $50 budget

    def __init__(self):
        api_key = self._load_api_key()
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=NEBIUS_BASE_URL,
        )
        self._usage_log: list[UsageRecord] = []

    # ──────────────────────────────────────────────────────────────────
    # Public inference API
    # ──────────────────────────────────────────────────────────────────

    async def complete_nano(
        self,
        prompt: str,
        system: str = "You are Synapse, an ambient desktop AI assistant.",
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> str:
        """Fast triage inference using Nemotron Nano. Target: < 300ms."""
        return await self._complete(
            model_key="nano",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def complete_ultra(
        self,
        prompt: str,
        system: str = "You are Synapse, an expert AI assistant for developers. Be precise, concise, and actionable.",
        temperature: float = 0.2,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> str:
        """Deep reasoning inference using Nemotron 3 Ultra."""
        if stream:
            raise NotImplementedError("Use complete_ultra_stream for streaming")
        return await self._complete(
            model_key="ultra",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def complete_ultra_stream(
        self,
        prompt: str,
        system: str = "You are Synapse, an expert AI assistant for developers.",
    ) -> AsyncGenerator[str, None]:
        """Streaming Nemotron Ultra — yields tokens as they arrive for responsive UI."""
        t0 = time.perf_counter()
        stream = await self._client.chat.completions.create(
            model=MODELS["ultra"],
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2048,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def embed(self, text: str) -> list[float]:
        """Generate embedding vector for PGVector storage/retrieval."""
        t0 = time.perf_counter()
        response = await self._client.embeddings.create(
            model=MODELS["embed"],
            input=text[:8000],  # Truncate to safe token limit
        )
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self._log_usage("embed", 0, 0, len(text) // 4, elapsed_ms)
        return response.data[0].embedding

    # ──────────────────────────────────────────────────────────────────
    # Usage tracking
    # ──────────────────────────────────────────────────────────────────

    @property
    def total_spend_estimate_usd(self) -> float:
        return sum(r.estimated_cost_usd for r in self._usage_log)

    def is_near_budget(self) -> bool:
        return self.total_spend_estimate_usd >= (50.0 - self.BUDGET_WARNING_USD)

    def usage_summary(self) -> dict:
        total_tokens = sum(r.total_tokens for r in self._usage_log)
        nano_calls = sum(1 for r in self._usage_log if r.model == "nano")
        ultra_calls = sum(1 for r in self._usage_log if r.model == "ultra")
        return {
            "total_tokens": total_tokens,
            "nano_calls": nano_calls,
            "ultra_calls": ultra_calls,
            "estimated_spend_usd": round(self.total_spend_estimate_usd, 4),
            "budget_remaining_usd": round(50.0 - self.total_spend_estimate_usd, 4),
        }

    # ──────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────

    async def _complete(self, model_key: str, messages: list, **kwargs) -> str:
        t0 = time.perf_counter()
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                response = await self._client.chat.completions.create(
                    model=MODELS[model_key],
                    messages=messages,
                    **kwargs,
                )
                elapsed_ms = (time.perf_counter() - t0) * 1000
                usage = response.usage
                self._log_usage(
                    model_key,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                    elapsed_ms,
                )
                return response.choices[0].message.content or ""
            except Exception as e:
                last_error = e
                if attempt < self.MAX_RETRIES - 1:
                    await __import__("asyncio").sleep(2 ** attempt)
        raise RuntimeError(f"Nebius API failed after {self.MAX_RETRIES} retries: {last_error}")

    def _log_usage(self, model: str, prompt_t: int, comp_t: int, total_t: int, latency_ms: float):
        self._usage_log.append(UsageRecord(
            model=model,
            prompt_tokens=prompt_t,
            completion_tokens=comp_t,
            total_tokens=total_t,
            latency_ms=latency_ms,
        ))
        if self.is_near_budget():
            print(f"[BUDGET WARNING] Estimated spend: ${self.total_spend_estimate_usd:.3f} / $50.00")

    @staticmethod
    def _load_api_key() -> str:
        """Load API key from env var or Windows Credential Manager."""
        key = os.environ.get("NEBIUS_API_KEY")
        if key:
            return key
        try:
            import keyring
            key = keyring.get_password("synapse", "NEBIUS_API_KEY")
            if key:
                return key
        except ImportError:
            pass
        raise ValueError(
            "NEBIUS_API_KEY not found. Set it in .env or Windows Credential Manager "
            "(credential name: 'synapse', username: 'NEBIUS_API_KEY')"
        )
