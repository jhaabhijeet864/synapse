"""
core/config.py
──────────────
App configuration & environment parsing.
All secrets loaded from .env or Windows Credential Manager — never hardcoded.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


def _env_int(key: str, default: int) -> int:
    try:
        return int(float(os.environ.get(key, default)))
    except (ValueError, TypeError):
        return default


@dataclass
class Settings:
    # ── Server ──────────────────────────────────────────────────────
    host: str = "127.0.0.1"
    port: int = 8420

    # ── Nebius ──────────────────────────────────────────────────────
    nebius_api_key: str = field(default_factory=lambda: _env("NEBIUS_API_KEY"))
    nebius_pgvector_url: str = field(default_factory=lambda: _env("NEBIUS_PGVECTOR_URL"))

    # ── Tavily ──────────────────────────────────────────────────────
    tavily_api_key: str = field(default_factory=lambda: _env("TAVILY_API_KEY"))

    # ── Capture tuning (overridable via SYNAPSE_* env vars, see .env.example) ──
    ocr_poll_interval_s: float = field(default_factory=lambda: _env_float("SYNAPSE_OCR_POLL_INTERVAL", 5.0))
    focus_poll_interval_s: float = field(default_factory=lambda: _env_float("SYNAPSE_FOCUS_POLL_INTERVAL", 10.0))
    trigger_emit_threshold: int = field(default_factory=lambda: _env_int("SYNAPSE_TRIGGER_THRESHOLD", 60))
    suppression_cooldown_s: int = field(default_factory=lambda: _env_int("SYNAPSE_SUPPRESSION_COOLDOWN", 60))

    # ── Budget ───────────────────────────────────────────────────────
    nebius_budget_usd: float = 50.0
    budget_warning_usd: float = 5.0   # Warn at $45 spent

    # ── Paths ────────────────────────────────────────────────────────
    notes_dir: Path = field(default_factory=lambda: Path.home() / "synapse_notes")
    log_dir: Path = field(default_factory=lambda: Path.home() / ".synapse" / "logs")

    def validate(self) -> None:
        missing = []
        if not self.nebius_api_key:
            missing.append("NEBIUS_API_KEY")
        if not self.nebius_pgvector_url:
            missing.append("NEBIUS_PGVECTOR_URL")
        if not self.tavily_api_key:
            missing.append("TAVILY_API_KEY")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}\n"
                             "Copy .env.example to .env and fill in your keys.")


# Load .env file if present
def _load_dotenv() -> None:
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()
settings = Settings()
