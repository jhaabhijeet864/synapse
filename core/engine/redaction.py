"""
core/engine/redaction.py
────────────────────────
Local PII & secret scrubber.

Runs deterministically BEFORE any context leaves the machine.
Zero cloud calls — pure regex + pattern matching.

Scrubbed text never reaches Nebius — only safe summaries.
"""

import re

PATTERNS = {
    'api_key': r"(?i)\b(api[_-]?key|bearer)\b\s*[:=]?\s*['\"]?[A-Za-z0-9_\-\.]{16,}['\"]?",
    'jwt': r"ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*",
    'private_key': r"-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]+?-----END (?:RSA )?PRIVATE KEY-----",
    'db_connection': r"postgres(?:ql)?://[^\s'\"@]+@[^\s'\"]+",
    'password': r"(?i)\b(password|passwd|secret)\b\s*[:=]\s*['\"]?[^'\"\s]+['\"]?",
}


def redact_sensitive_data(text: str) -> str:
    cleaned = text
    for label, pattern in PATTERNS.items():
        cleaned = re.sub(pattern, f"[REDACTED_{label.upper()}]", cleaned)
    return cleaned


def scrub(text: str) -> str:
    """Legacy alias kept for core/nebius/router.py."""
    return redact_sensitive_data(text)
