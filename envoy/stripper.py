"""Strip keys from a .env dict by name, pattern, or tag prefix."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


class StripError(Exception):
    """Raised when stripping fails."""


@dataclass
class StripResult:
    env: Dict[str, str]
    stripped_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.stripped_keys)

    def summary(self) -> str:
        if not self.stripped_keys:
            return "No keys stripped."
        keys = ", ".join(self.stripped_keys)
        return f"Stripped {len(self.stripped_keys)} key(s): {keys}"


def strip(
    env: Dict[str, str],
    keys: Optional[Iterable[str]] = None,
    patterns: Optional[Iterable[str]] = None,
    prefix: Optional[str] = None,
) -> StripResult:
    """Return a new env dict with matching keys removed.

    Args:
        env: Source key/value mapping.
        keys: Exact key names to remove.
        patterns: Regex patterns; any matching key is removed.
        prefix: Remove all keys whose name starts with this prefix.

    Returns:
        StripResult with the filtered env and list of removed keys.
    """
    exact: set[str] = set(keys) if keys else set()
    compiled = [re.compile(p) for p in (patterns or [])]

    result_env: Dict[str, str] = {}
    stripped: List[str] = []

    for key, value in env.items():
        remove = False
        if key in exact:
            remove = True
        elif prefix and key.startswith(prefix):
            remove = True
        elif any(rx.search(key) for rx in compiled):
            remove = True

        if remove:
            stripped.append(key)
        else:
            result_env[key] = value

    return StripResult(env=result_env, stripped_keys=stripped)
