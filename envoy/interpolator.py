"""Variable interpolation for .env files.

Supports ${VAR} and $VAR syntax with optional default values via ${VAR:-default}.
"""

from __future__ import annotations

import re
from typing import Dict, Optional

_BRACE_RE = re.compile(r'\$\{([^}]+)\}')
_BARE_RE = re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)')


class InterpolationError(Exception):
    """Raised when a required variable reference cannot be resolved."""

    def __init__(self, key: str, ref: str) -> None:
        self.key = key
        self.ref = ref
        super().__init__(f"Key '{key}': unresolved reference '${{{ref}}}'")


def _resolve_brace(match: re.Match, env: Dict[str, str], strict: bool) -> str:
    """Resolve a ${VAR} or ${VAR:-default} reference."""
    inner = match.group(1)
    if ':-' in inner:
        var, default = inner.split(':-', 1)
        return env.get(var.strip(), default)
    var = inner.strip()
    if var in env:
        return env[var]
    if strict:
        raise InterpolationError('<unknown>', var)
    return match.group(0)  # leave unresolved


def _resolve_bare(match: re.Match, env: Dict[str, str]) -> str:
    """Resolve a $VAR reference."""
    var = match.group(1)
    return env.get(var, match.group(0))


def interpolate_value(
    value: str,
    env: Dict[str, str],
    *,
    strict: bool = False,
) -> str:
    """Expand variable references in *value* using *env* as the lookup table.

    Args:
        value:  The raw string that may contain ``$VAR`` or ``${VAR}`` tokens.
        env:    Mapping of variable names to their (already resolved) values.
        strict: When *True*, raise :class:`InterpolationError` for any
                unresolvable reference; otherwise leave the token as-is.

    Returns:
        The fully interpolated string.
    """
    def brace_sub(m: re.Match) -> str:
        return _resolve_brace(m, env, strict)

    result = _BRACE_RE.sub(brace_sub, value)
    result = _BARE_RE.sub(lambda m: _resolve_bare(m, env), result)
    return result


def interpolate_env(
    pairs: Dict[str, str],
    *,
    base: Optional[Dict[str, str]] = None,
    strict: bool = False,
) -> Dict[str, str]:
    """Interpolate an entire env mapping in definition order.

    Each key is resolved against all previously resolved keys plus the
    optional *base* mapping (e.g. the real process environment).

    Args:
        pairs:  Ordered dict of raw key→value pairs from the parser.
        base:   Optional external variables available for interpolation.
        strict: Propagated to :func:`interpolate_value`.

    Returns:
        A new dict with all values interpolated.
    """
    resolved: Dict[str, str] = dict(base or {})
    output: Dict[str, str] = {}
    for key, raw_value in pairs.items():
        value = interpolate_value(raw_value, resolved, strict=strict)
        resolved[key] = value
        output[key] = value
    return output
