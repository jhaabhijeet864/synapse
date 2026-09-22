"""
core/logging_config.py
────────────────────────
Structured JSON logger for Synapse telemetry.

Emits JSON lines compatible with the spec:
  {"timestamp": "2026-09-23T00:45:10Z", "stage": "nano_triage", "latency_ms": 118, "escalate": true}
  {"timestamp": "2026-09-23T00:45:11Z", "stage": "pgvector_lookup", "similarity": 0.88, "latency_ms": 22}
  {"timestamp": "2026-09-23T00:45:12Z", "stage": "nemotron_ultra", "tokens_in": 842, "tokens_out": 190, "latency_ms": 840}
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        # Inject any extra fields passed via extra dict
        for key in ("stage", "latency_ms", "escalate", "similarity", "tokens_in", "tokens_out"):
            if key in record.__dict__:
                entry[key] = record.__dict__[key]
        return json.dumps(entry)


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure the root logger with JSON output to stderr."""
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    root.handlers = [handler]

    return root