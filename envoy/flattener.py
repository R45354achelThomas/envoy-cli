"""Flatten nested or prefixed env keys into a single-level dict with optional key transformation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class FlattenError(Exception):
    """Raised when flattening cannot be completed."""


@dataclass
class FlattenResult:
    flattened: Dict[str, str]
    renamed: List[str] = field(default_factory=list)  # keys whose names changed
    skipped: List[str] = field(default_factory=list)   # keys dropped due to collision

    def has_changes(self) -> bool:
        return bool(self.renamed or self.skipped)

    def summary(self) -> str:
        parts = [f"{len(self.flattened)} key(s) in result"]
        if self.renamed:
            parts.append(f"{len(self.renamed)} renamed")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped (collision)")
        return ", ".join(parts)


def flatten(
    env: Dict[str, str],
    separator: str = "__",
    strip_prefix: Optional[str] = None,
    lowercase: bool = False,
    collision: str = "skip",  # "skip" | "overwrite"
) -> FlattenResult:
    """Flatten env keys by collapsing a separator-based hierarchy.

    Args:
        env: Source key/value pairs.
        separator: Segment separator used to detect hierarchy (default '__').
        strip_prefix: If given, remove this prefix (case-insensitive) from every key.
        lowercase: Convert resulting keys to lowercase.
        collision: What to do when two source keys map to the same output key.
                   'skip' keeps the first, 'overwrite' keeps the last.
    """
    if collision not in ("skip", "overwrite"):
        raise FlattenError(f"Unknown collision strategy: {collision!r}")
    if not separator:
        raise FlattenError("separator must be a non-empty string")

    result: Dict[str, str] = {}
    renamed: List[str] = []
    skipped: List[str] = []

    for key, value in env.items():
        new_key = key

        # Strip prefix
        if strip_prefix:
            prefix_upper = strip_prefix.upper()
            if new_key.upper().startswith(prefix_upper):
                new_key = new_key[len(strip_prefix):]
                if new_key.startswith(separator):
                    new_key = new_key[len(separator):]

        # Replace separator sequences with a single underscore
        new_key = new_key.replace(separator, "_")

        if lowercase:
            new_key = new_key.lower()

        if new_key != key:
            renamed.append(key)

        if new_key in result:
            if collision == "skip":
                skipped.append(key)
                continue
            # overwrite — replace existing
            result[new_key] = value
        else:
            result[new_key] = value

    return FlattenResult(flattened=result, renamed=renamed, skipped=skipped)
