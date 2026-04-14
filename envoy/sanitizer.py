"""Sanitize .env file contents by redacting or removing sensitive keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.diff import _is_secret


class SanitizeError(Exception):
    """Raised when sanitization cannot be completed."""


@dataclass
class SanitizeResult:
    """Result of a sanitize operation."""

    original: Dict[str, str]
    sanitized: Dict[str, str]
    redacted_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.redacted_keys or self.removed_keys)

    def summary(self) -> str:
        parts: List[str] = []
        if self.redacted_keys:
            parts.append(f"Redacted {len(self.redacted_keys)} key(s): {', '.join(sorted(self.redacted_keys))}")
        if self.removed_keys:
            parts.append(f"Removed {len(self.removed_keys)} key(s): {', '.join(sorted(self.removed_keys))}")
        if not parts:
            return "No changes made."
        return "; ".join(parts) + "."


REDACT_PLACEHOLDER = "REDACTED"


def sanitize(
    env: Dict[str, str],
    *,
    redact: bool = True,
    remove: bool = False,
    extra_keys: Optional[List[str]] = None,
    placeholder: str = REDACT_PLACEHOLDER,
) -> SanitizeResult:
    """Return a sanitized copy of *env*.

    Parameters
    ----------
    env:
        Parsed key/value mapping to sanitize.
    redact:
        Replace secret values with *placeholder* (default ``True``).
    remove:
        Remove secret keys entirely instead of redacting (overrides *redact*).
    extra_keys:
        Additional key names to treat as secrets regardless of heuristics.
    placeholder:
        String used when redacting a value.
    """
    extra = set(k.upper() for k in (extra_keys or []))
    sanitized: Dict[str, str] = {}
    redacted: List[str] = []
    removed: List[str] = []

    for key, value in env.items():
        is_sensitive = _is_secret(key) or key.upper() in extra
        if is_sensitive:
            if remove:
                removed.append(key)
                continue
            elif redact:
                sanitized[key] = placeholder
                redacted.append(key)
                continue
        sanitized[key] = value

    return SanitizeResult(
        original=dict(env),
        sanitized=sanitized,
        redacted_keys=redacted,
        removed_keys=removed,
    )
