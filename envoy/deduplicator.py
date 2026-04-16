"""Deduplicator: remove duplicate values from an env mapping."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class DeduplicateError(Exception):
    pass


@dataclass
class DeduplicateResult:
    env: Dict[str, str]
    removed_keys: List[str] = field(default_factory=list)
    kept_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.removed_keys)

    def summary(self) -> str:
        if not self.has_changes():
            return "No duplicate values found."
        return (
            f"Removed {len(self.removed_keys)} key(s) with duplicate values: "
            + ", ".join(self.removed_keys)
        )


def deduplicate(
    env: Dict[str, str],
    keep: str = "first",
    ignore_keys: Optional[List[str]] = None,
) -> DeduplicateResult:
    """Remove keys whose values are duplicates of an already-seen value.

    Args:
        env: Ordered dict of key/value pairs.
        keep: 'first' keeps the first occurrence; 'last' keeps the last.
        ignore_keys: Keys to exclude from deduplication logic entirely.
    """
    if keep not in ("first", "last"):
        raise DeduplicateError(f"Invalid keep strategy: {keep!r}. Use 'first' or 'last'.")

    ignore = set(ignore_keys or [])
    items = list(env.items())

    if keep == "last":
        items = items[::-1]

    seen_values: Dict[str, str] = {}
    removed: List[str] = []

    for key, value in items:
        if key in ignore:
            continue
        if value in seen_values:
            removed.append(key)
        else:
            seen_values[value] = key

    removed_set = set(removed)
    deduped = {k: v for k, v in env.items() if k not in removed_set}
    kept = [k for k in deduped if k not in ignore]

    return DeduplicateResult(env=deduped, removed_keys=removed, kept_keys=kept)
