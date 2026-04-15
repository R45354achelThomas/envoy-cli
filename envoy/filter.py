"""Filter env key-value pairs by pattern, prefix, tag, or value presence."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class FilterError(Exception):
    pass


@dataclass
class FilterResult:
    matched: Dict[str, str]
    excluded: Dict[str, str]

    def has_matches(self) -> bool:
        return bool(self.matched)

    def summary(self) -> str:
        return (
            f"{len(self.matched)} key(s) matched, "
            f"{len(self.excluded)} key(s) excluded"
        )


def filter_env(
    env: Dict[str, str],
    *,
    pattern: Optional[str] = None,
    prefix: Optional[str] = None,
    exclude_empty: bool = False,
    invert: bool = False,
) -> FilterResult:
    """Return a FilterResult partitioning *env* into matched / excluded.

    Args:
        env: Source key-value mapping.
        pattern: Regex applied to key names (case-insensitive).
        prefix: Only keep keys that start with this string (case-insensitive).
        exclude_empty: Drop keys whose value is an empty string.
        invert: Swap matched and excluded sets.
    """
    if pattern is not None:
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as exc:
            raise FilterError(f"Invalid regex pattern {pattern!r}: {exc}") from exc
    else:
        compiled = None

    matched: Dict[str, str] = {}
    excluded: Dict[str, str] = {}

    for key, value in env.items():
        keep = True

        if compiled is not None and not compiled.search(key):
            keep = False

        if prefix is not None and not key.upper().startswith(prefix.upper()):
            keep = False

        if exclude_empty and value == "":
            keep = False

        if invert:
            keep = not keep

        if keep:
            matched[key] = value
        else:
            excluded[key] = value

    return FilterResult(matched=matched, excluded=excluded)
