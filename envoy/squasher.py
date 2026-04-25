"""Squash multiple .env files into a single merged output, deduplicating keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class SquashError(Exception):
    """Raised when squashing fails."""


@dataclass
class SquashResult:
    env: Dict[str, str]
    sources: Dict[str, str]          # key -> filename that won
    overridden: List[Tuple[str, str, str]] = field(default_factory=list)  # (key, old_file, new_file)

    def has_overrides(self) -> bool:
        return bool(self.overridden)

    def summary(self) -> str:
        total = len(self.env)
        over = len(self.overridden)
        return f"{total} key(s) in final output; {over} key(s) overridden across files."


def squash(
    envs: List[Tuple[str, Dict[str, str]]],
    *,
    last_wins: bool = True,
) -> SquashResult:
    """Squash a list of (filename, env_dict) pairs into one env.

    Parameters
    ----------
    envs:
        Ordered list of ``(label, mapping)`` pairs.  Earlier entries have
        lower priority when *last_wins* is ``True`` (the default).
    last_wins:
        When ``True`` the rightmost file wins on conflict.  When ``False``
        the first occurrence is kept (first-wins semantics).
    """
    if not envs:
        raise SquashError("At least one env mapping is required.")

    result: Dict[str, str] = {}
    sources: Dict[str, str] = {}
    overridden: List[Tuple[str, str, str]] = []

    for label, mapping in envs:
        for key, value in mapping.items():
            if key in result:
                if last_wins:
                    overridden.append((key, sources[key], label))
                    result[key] = value
                    sources[key] = label
                # else: first-wins — keep existing, do nothing
            else:
                result[key] = value
                sources[key] = label

    return SquashResult(env=result, sources=sources, overridden=overridden)
