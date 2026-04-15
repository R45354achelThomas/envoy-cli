"""Normalize .env file keys and values to a canonical form."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class NormalizeError(Exception):
    """Raised when normalization cannot proceed."""


@dataclass
class NormalizeResult:
    """Result of a normalization pass."""

    normalized: Dict[str, str]
    changed_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changed_keys)

    def summary(self) -> str:
        if not self.has_changes():
            return "No changes — env is already normalized."
        return (
            f"{len(self.changed_keys)} key(s) normalized: "
            + ", ".join(self.changed_keys)
        )


def normalize(
    env: Dict[str, str],
    *,
    uppercase_keys: bool = True,
    strip_values: bool = True,
    replace_spaces_in_keys: bool = True,
) -> NormalizeResult:
    """Return a normalized copy of *env*.

    Parameters
    ----------
    env:
        Source key/value mapping.
    uppercase_keys:
        Convert all keys to UPPER_CASE.
    strip_values:
        Strip leading/trailing whitespace from values.
    replace_spaces_in_keys:
        Replace spaces in keys with underscores.
    """
    if not isinstance(env, dict):
        raise NormalizeError("env must be a dict")

    normalized: Dict[str, str] = {}
    changed_keys: List[str] = []

    for raw_key, raw_value in env.items():
        new_key = raw_key
        new_value = raw_value

        if replace_spaces_in_keys:
            new_key = new_key.replace(" ", "_")
        if uppercase_keys:
            new_key = new_key.upper()
        if strip_values:
            new_value = new_value.strip()

        if new_key != raw_key or new_value != raw_value:
            changed_keys.append(raw_key)

        normalized[new_key] = new_value

    return NormalizeResult(normalized=normalized, changed_keys=changed_keys)
