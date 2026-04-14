"""Trim whitespace and normalize values in .env files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class TrimError(Exception):
    """Raised when trimming fails."""


@dataclass
class TrimResult:
    """Result of a trim operation."""

    trimmed: Dict[str, str] = field(default_factory=dict)
    changed_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return len(self.changed_keys) > 0

    def summary(self) -> str:
        if not self.has_changes():
            return "No changes — all values already clean."
        keys = ", ".join(self.changed_keys)
        return f"Trimmed {len(self.changed_keys)} key(s): {keys}"


def trim(
    env: Dict[str, str],
    *,
    strip_keys: bool = True,
    strip_values: bool = True,
    normalize_empty: bool = False,
) -> TrimResult:
    """Return a TrimResult with whitespace removed from keys and/or values.

    Args:
        env: Mapping of key -> value to process.
        strip_keys: Strip leading/trailing whitespace from keys.
        strip_values: Strip leading/trailing whitespace from values.
        normalize_empty: Replace whitespace-only values with empty string.

    Returns:
        TrimResult with cleaned mapping and list of changed keys.
    """
    trimmed: Dict[str, str] = {}
    changed_keys: List[str] = []

    for raw_key, raw_value in env.items():
        key = raw_key.strip() if strip_keys else raw_key
        value = raw_value.strip() if strip_values else raw_value

        if normalize_empty and value.strip() == "":
            value = ""

        trimmed[key] = value

        if key != raw_key or value != raw_value:
            changed_keys.append(key)

    return TrimResult(trimmed=trimmed, changed_keys=changed_keys)
