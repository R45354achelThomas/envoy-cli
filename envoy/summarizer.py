"""Summarize a .env file into a human-readable statistics report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envoy.diff import _is_secret


class SummarizeError(Exception):
    """Raised when summarization fails."""


@dataclass
class SummarizeResult:
    total: int
    secret_count: int
    empty_count: int
    unique_values: int
    top_prefixes: Dict[str, int] = field(default_factory=dict)
    longest_key: str = ""
    shortest_key: str = ""
    keys: List[str] = field(default_factory=list)

    def has_secrets(self) -> bool:
        return self.secret_count > 0

    def has_empty(self) -> bool:
        return self.empty_count > 0

    def summary(self) -> str:
        lines = [
            f"Total keys   : {self.total}",
            f"Secrets      : {self.secret_count}",
            f"Empty values : {self.empty_count}",
            f"Unique values: {self.unique_values}",
            f"Longest key  : {self.longest_key!r}",
            f"Shortest key : {self.shortest_key!r}",
        ]
        if self.top_prefixes:
            lines.append("Top prefixes :")
            for prefix, count in sorted(
                self.top_prefixes.items(), key=lambda x: -x[1]
            ):
                lines.append(f"  {prefix}_  ({count})")
        return "\n".join(lines)


def _extract_prefix(key: str) -> str | None:
    """Return the first segment before '_', or None if no underscore."""
    if "_" in key:
        return key.split("_", 1)[0]
    return None


def summarize(env: Dict[str, str]) -> SummarizeResult:
    """Produce a SummarizeResult for the given env mapping."""
    if not isinstance(env, dict):
        raise SummarizeError("env must be a dict")

    keys = list(env.keys())
    total = len(keys)

    if total == 0:
        return SummarizeResult(
            total=0,
            secret_count=0,
            empty_count=0,
            unique_values=0,
            top_prefixes={},
            longest_key="",
            shortest_key="",
            keys=[],
        )

    secret_count = sum(1 for k in keys if _is_secret(k))
    empty_count = sum(1 for v in env.values() if v == "")
    unique_values = len(set(env.values()))

    longest_key = max(keys, key=len)
    shortest_key = min(keys, key=len)

    prefix_counts: Dict[str, int] = {}
    for k in keys:
        p = _extract_prefix(k)
        if p:
            prefix_counts[p] = prefix_counts.get(p, 0) + 1

    # Keep only prefixes that appear more than once
    top_prefixes = {p: c for p, c in prefix_counts.items() if c > 1}

    return SummarizeResult(
        total=total,
        secret_count=secret_count,
        empty_count=empty_count,
        unique_values=unique_values,
        top_prefixes=top_prefixes,
        longest_key=longest_key,
        shortest_key=shortest_key,
        keys=keys,
    )
