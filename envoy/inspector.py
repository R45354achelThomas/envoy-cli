"""Inspect a .env file and produce a human-readable summary of its contents."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from envoy.diff import _is_secret


class InspectError(Exception):
    """Raised when inspection cannot be completed."""


@dataclass
class InspectResult:
    total: int
    secret_keys: List[str]
    empty_keys: List[str]
    longest_key: str
    shortest_key: str
    env: Dict[str, str]
    _key_lengths: Dict[str, int] = field(default_factory=dict, repr=False)

    @property
    def has_secrets(self) -> bool:
        return len(self.secret_keys) > 0

    @property
    def has_empty(self) -> bool:
        return len(self.empty_keys) > 0

    def summary(self) -> str:
        lines = [
            f"Total keys   : {self.total}",
            f"Secret keys  : {len(self.secret_keys)}",
            f"Empty keys   : {len(self.empty_keys)}",
            f"Longest key  : {self.longest_key!r} ({len(self.longest_key)} chars)",
            f"Shortest key : {self.shortest_key!r} ({len(self.shortest_key)} chars)",
        ]
        return "\n".join(lines)


def inspect(env: Dict[str, str]) -> InspectResult:
    """Inspect *env* and return an :class:`InspectResult`."""
    if not isinstance(env, dict):
        raise InspectError("env must be a dict")

    keys = list(env.keys())
    if not keys:
        return InspectResult(
            total=0,
            secret_keys=[],
            empty_keys=[],
            longest_key="",
            shortest_key="",
            env=env,
        )

    secret_keys = [k for k in keys if _is_secret(k)]
    empty_keys = [k for k in keys if env[k] == ""]
    longest_key = max(keys, key=len)
    shortest_key = min(keys, key=len)

    return InspectResult(
        total=len(keys),
        secret_keys=secret_keys,
        empty_keys=empty_keys,
        longest_key=longest_key,
        shortest_key=shortest_key,
        env=env,
    )
