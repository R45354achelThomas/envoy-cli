"""Redactor: replace secret values in a .env dict with a placeholder or custom string."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.diff import _is_secret

DEFAULT_PLACEHOLDER = "[REDACTED]"


class RedactError(Exception):
    """Raised when redaction cannot be completed."""


@dataclass
class RedactResult:
    """Outcome of a redact operation."""

    original: Dict[str, str]
    redacted: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.redacted_keys)

    def summary(self) -> str:
        if not self.has_changes():
            return "No secrets detected; nothing redacted."
        keys = ", ".join(sorted(self.redacted_keys))
        return f"Redacted {len(self.redacted_keys)} secret key(s): {keys}"


def redact(
    env: Dict[str, str],
    placeholder: str = DEFAULT_PLACEHOLDER,
    extra_keys: Optional[List[str]] = None,
    keys_only: Optional[List[str]] = None,
) -> RedactResult:
    """Return a copy of *env* with secret values replaced by *placeholder*.

    Args:
        env:         The parsed environment dict.
        placeholder: String to substitute for secret values.
        extra_keys:  Additional key names to treat as secrets regardless of
                     heuristic detection.
        keys_only:   If provided, only redact keys in this list (still subject
                     to the secret heuristic unless the key is in *extra_keys*).
    """
    if not isinstance(env, dict):
        raise RedactError("env must be a dict")

    extra = set(k.upper() for k in (extra_keys or []))
    restrict = set(k.upper() for k in (keys_only or [])) if keys_only is not None else None

    redacted: Dict[str, str] = {}
    redacted_keys: List[str] = []

    for key, value in env.items():
        upper = key.upper()
        in_restrict = restrict is None or upper in restrict
        is_sec = _is_secret(key) or upper in extra

        if in_restrict and is_sec:
            redacted[key] = placeholder
            redacted_keys.append(key)
        else:
            redacted[key] = value

    return RedactResult(
        original=dict(env),
        redacted=redacted,
        redacted_keys=redacted_keys,
    )
