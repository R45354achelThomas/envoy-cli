"""Split a single .env file into multiple files based on key prefixes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SplitError(Exception):
    """Raised when splitting fails."""


@dataclass
class SplitResult:
    """Result of a split operation."""

    buckets: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    @property
    def has_ungrouped(self) -> bool:
        return bool(self.ungrouped)

    @property
    def bucket_names(self) -> List[str]:
        return sorted(self.buckets.keys())

    def summary(self) -> str:
        parts = [f"{name}: {len(keys)} key(s)" for name, keys in sorted(self.buckets.items())]
        if self.ungrouped:
            parts.append(f"(ungrouped): {len(self.ungrouped)} key(s)")
        return ", ".join(parts) if parts else "no keys"


def split(
    env: Dict[str, str],
    prefixes: Optional[List[str]] = None,
    separator: str = "_",
    keep_prefix: bool = True,
) -> SplitResult:
    """Split *env* into buckets by key prefix.

    Parameters
    ----------
    env:        Flat mapping of key -> value.
    prefixes:   Explicit list of prefixes to split on.  When *None* every
                unique first-segment (split on *separator*) becomes a bucket.
    separator:  Character used to identify the prefix boundary.
    keep_prefix: When *False* the prefix + separator are stripped from the
                 key in the output bucket.
    """
    if not isinstance(env, dict):
        raise SplitError("env must be a dict")

    result = SplitResult()

    # Build the set of prefixes to match against.
    if prefixes is not None:
        active_prefixes = [p.upper() for p in prefixes]
    else:
        active_prefixes = []
        for key in env:
            if separator in key:
                segment = key.split(separator, 1)[0].upper()
                if segment not in active_prefixes:
                    active_prefixes.append(segment)

    for key, value in env.items():
        matched = False
        for prefix in active_prefixes:
            token = prefix + separator
            if key.upper().startswith(token):
                bucket_key = key if keep_prefix else key[len(token):]
                result.buckets.setdefault(prefix, {})[bucket_key] = value
                matched = True
                break
        if not matched:
            result.ungrouped[key] = value

    return result
