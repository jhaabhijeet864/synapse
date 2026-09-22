"""
core/engine/redaction.py
────────────────────────
Local PII & secret scrubber.

Runs deterministically BEFORE any context leaves the machine.
Zero cloud calls — pure regex + pattern matching.

Scrubs:
  - API keys & tokens (OpenAI, AWS, GitHub, JWT, etc.)
  - .env variable values
  - Passwords in connection strings
  - Credit card numbers
  - Email addresses (optional, configurable)
  - IP addresses (optional)

Architecture principle: Raw user data NEVER leaves the machine.
Only scrubbed summaries reach Nebius.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class RedactionResult:
    original_length: int
    scrubbed_text: str
    redaction_count: int
    categories_hit: list[str]


class Redactor:
    """
    Applies a prioritized regex pipeline to scrub sensitive content
    from any text before cloud transmission.

    All replacements use descriptive placeholders so Nemotron still
    understands the structure of what was redacted.

    Usage:
        r = Redactor()
        result = r.scrub(raw_text)
        safe_text = result.scrubbed_text
    """

    # Each rule: (category_name, compiled_regex, replacement_string)
    RULES: list[tuple[str, re.Pattern, str]] = [

        # ── API Keys & Secrets ────────────────────────────────────────

        # OpenAI / Anthropic style keys
        ("api_key", re.compile(r"sk-[A-Za-z0-9]{20,60}", re.IGNORECASE), "[REDACTED_API_KEY]"),

        # AWS Access Key ID
        ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED_AWS_KEY]"),

        # AWS Secret Access Key (40 chars alphanumeric+symbols)
        ("aws_secret", re.compile(r"(?<![A-Za-z0-9])[A-Za-z0-9/+]{40}(?![A-Za-z0-9/+])"), "[REDACTED_AWS_SECRET]"),

        # GitHub PAT
        ("github_token", re.compile(r"ghp_[A-Za-z0-9]{36}"), "[REDACTED_GITHUB_TOKEN]"),

        # Generic Bearer token in Authorization header
        ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),

        # JWT (three base64url segments separated by dots)
        ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), "[REDACTED_JWT]"),

        # Nebius API key pattern (similar to OpenAI)
        ("nebius_key", re.compile(r"nbk-[A-Za-z0-9]{20,60}", re.IGNORECASE), "[REDACTED_NEBIUS_KEY]"),

        # ── Connection Strings ────────────────────────────────────────

        # PostgreSQL/MySQL DSN with password
        ("db_dsn", re.compile(
            r"(postgresql|postgres|mysql|mongodb)://([^:]+):([^@]+)@",
            re.IGNORECASE
        ), r"\1://\2:[REDACTED_PASSWORD]@"),

        # Generic password= in query strings / config
        ("password_kv", re.compile(
            r"(password|passwd|pwd)\s*[=:]\s*['\"]?([^\s'\"&,;]+)['\"]?",
            re.IGNORECASE
        ), r"\1=[REDACTED_PASSWORD]"),

        # ── .env file values ─────────────────────────────────────────

        # KEY=VALUE patterns typical in .env files
        ("dotenv_secret", re.compile(
            r"^((?:API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE|KEY|AUTH)[_A-Z0-9]*)\s*=\s*(.+)$",
            re.MULTILINE | re.IGNORECASE
        ), r"\1=[REDACTED]"),

        # ── Personal Data (optional, default ON) ─────────────────────

        # Email addresses
        ("email", re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
        ), "[REDACTED_EMAIL]"),

        # Credit card numbers (Luhn-detectable via pattern, not validated)
        ("credit_card", re.compile(
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b"
        ), "[REDACTED_CARD]"),

        # Private IP ranges in sensitive context (optional — disabled by default)
        # ("private_ip", re.compile(r"\b(192\.168|10\.|172\.(1[6-9]|2[0-9]|3[01]))\.\d+\.\d+\b"), "[REDACTED_IP]"),
    ]

    def __init__(self, redact_emails: bool = True, redact_cards: bool = True):
        self._active_rules = list(self.RULES)
        if not redact_emails:
            self._active_rules = [r for r in self._active_rules if r[0] != "email"]
        if not redact_cards:
            self._active_rules = [r for r in self._active_rules if r[0] != "credit_card"]

    def scrub(self, text: str) -> RedactionResult:
        """
        Apply all active redaction rules to text.
        Returns a RedactionResult with the scrubbed text and metadata.
        """
        if not text:
            return RedactionResult(0, "", 0, [])

        original_length = len(text)
        scrubbed = text
        hit_categories: list[str] = []
        total_count = 0

        for category, pattern, replacement in self._active_rules:
            new_text, count = pattern.subn(replacement, scrubbed)
            if count > 0:
                scrubbed = new_text
                hit_categories.append(category)
                total_count += count

        return RedactionResult(
            original_length=original_length,
            scrubbed_text=scrubbed,
            redaction_count=total_count,
            categories_hit=hit_categories,
        )

    def is_clean(self, text: str) -> bool:
        """Quick check: returns True if no sensitive patterns found."""
        for _, pattern, _ in self._active_rules:
            if pattern.search(text):
                return False
        return True


# Module-level default instance for convenience
_default = Redactor()

def scrub(text: str) -> str:
    """Convenience function — scrub text with default settings."""
    return _default.scrub(text).scrubbed_text
