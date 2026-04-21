"""Count and report statistics about keys in a .env mapping."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envoy.diff import _is_secret


class CountError(Exception):
    """Raised when counting fails."""


@dataclass
class CountResult:
    total: int
    secret_count: int
    empty_count: int
    non_empty_count: int
    prefix_counts: Dict[str, int] = field(default_factory=dict)
    longest_key: str = ""
    shortest_key: str = ""
    average_value_length: float = 0.0

    def has_secrets(self) -> bool:
        return self.secret_count > 0

    def has_empty(self) -> bool:
        return self.empty_count > 0

    def summary(self) -> str:
        lines: List[str] = [
            f"Total keys      : {self.total}",
            f"Secret keys     : {self.secret_count}",
            f"Empty values    : {self.empty_count}",
            f"Non-empty values: {self.non_empty_count}",
            f"Longest key     : {self.longest_key!r}",
            f"Shortest key    : {self.shortest_key!r}",
            f"Avg value length: {self.average_value_length:.1f}",
        ]
        if self.prefix_counts:
            lines.append("Prefix breakdown:")
            for prefix, cnt in sorted(self.prefix_counts.items()):
                lines.append(f"  {prefix}_* : {cnt}")
        return "\n".join(lines)


def count(env: Dict[str, str], separator: str = "_") -> CountResult:
    """Compute statistics for *env*.

    Args:
        env: Mapping of key -> value.
        separator: Character used to detect key prefixes (default ``"_"``).

    Returns:
        A :class:`CountResult` with all computed statistics.
    """
    if not isinstance(env, dict):
        raise CountError("env must be a dict")

    keys = list(env.keys())
    total = len(keys)

    if total == 0:
        return CountResult(
            total=0,
            secret_count=0,
            empty_count=0,
            non_empty_count=0,
        )

    secret_count = sum(1 for k in keys if _is_secret(k))
    empty_count = sum(1 for v in env.values() if v == "")
    non_empty_count = total - empty_count

    sorted_by_len = sorted(keys, key=len)
    shortest_key = sorted_by_len[0]
    longest_key = sorted_by_len[-1]

    value_lengths = [len(v) for v in env.values()]
    average_value_length = sum(value_lengths) / total

    prefix_counts: Dict[str, int] = {}
    for k in keys:
        if separator in k:
            prefix = k.split(separator, 1)[0]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

    return CountResult(
        total=total,
        secret_count=secret_count,
        empty_count=empty_count,
        non_empty_count=non_empty_count,
        prefix_counts=prefix_counts,
        longest_key=longest_key,
        shortest_key=shortest_key,
        average_value_length=average_value_length,
    )
