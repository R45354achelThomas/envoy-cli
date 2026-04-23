"""Scope filtering: restrict an env dict to keys matching a given scope/namespace."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ScopeError(Exception):
    """Raised when scoping cannot be performed."""


@dataclass
class ScopeResult:
    """Result of a scope operation."""

    scoped: Dict[str, str]
    dropped: List[str]
    scope: Optional[str]
    strip_prefix: bool

    def has_dropped(self) -> bool:
        return bool(self.dropped)

    def summary(self) -> str:
        kept = len(self.scoped)
        dropped = len(self.dropped)
        scope_label = f"'{self.scope}'" if self.scope else "<all>"
        return (
            f"Scope {scope_label}: {kept} key(s) kept, {dropped} key(s) dropped"
        )


def scope(
    env: Dict[str, str],
    scope: Optional[str] = None,
    separator: str = "_",
    strip_prefix: bool = True,
    case_sensitive: bool = False,
) -> ScopeResult:
    """Return only keys that belong to *scope*.

    Parameters
    ----------
    env:
        Source key/value mapping.
    scope:
        Prefix (namespace) to filter by, e.g. ``"DB"`` keeps ``DB_HOST``,
        ``DB_PORT``, …  When *None* or empty the full env is returned.
    separator:
        Character that separates the scope prefix from the rest of the key.
    strip_prefix:
        When *True* (default) the prefix + separator is removed from each
        kept key so ``DB_HOST`` becomes ``HOST``.
    case_sensitive:
        Whether prefix matching is case-sensitive (default: False).
    """
    if not env:
        return ScopeResult(scoped={}, dropped=[], scope=scope, strip_prefix=strip_prefix)

    if not scope:
        return ScopeResult(
            scoped=dict(env),
            dropped=[],
            scope=scope,
            strip_prefix=strip_prefix,
        )

    prefix = scope if case_sensitive else scope.upper()
    full_prefix = prefix + separator

    scoped: Dict[str, str] = {}
    dropped: List[str] = []

    for key, value in env.items():
        compare_key = key if case_sensitive else key.upper()
        if compare_key.startswith(full_prefix):
            new_key = key[len(full_prefix):] if strip_prefix else key
            if not new_key:
                dropped.append(key)
            else:
                scoped[new_key] = value
        else:
            dropped.append(key)

    return ScopeResult(
        scoped=scoped,
        dropped=dropped,
        scope=scope,
        strip_prefix=strip_prefix,
    )
