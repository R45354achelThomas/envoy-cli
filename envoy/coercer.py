"""coercer.py — Force-coerce env values to a target type with optional defaults."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class CoerceError(Exception):
    """Raised when a coercion operation fails fatally."""


@dataclass
class CoerceIssue:
    key: str
    raw_value: str
    target_type: str
    reason: str

    def __str__(self) -> str:
        return f"{self.key}: cannot coerce {self.raw_value!r} to {self.target_type} — {self.reason}"


@dataclass
class CoerceResult:
    env: Dict[str, Any]
    issues: List[CoerceIssue] = field(default_factory=list)
    coerced_keys: List[str] = field(default_factory=list)

    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        return (
            f"{len(self.coerced_keys)} key(s) coerced, "
            f"{len(self.issues)} issue(s)"
        )


_SUPPORTED = ("int", "float", "bool", "str")

_BOOL_TRUE = {"1", "true", "yes", "on"}
_BOOL_FALSE = {"0", "false", "no", "off"}


def _coerce_one(
    key: str,
    raw: str,
    target: str,
    default: Optional[str],
) -> tuple[Any, Optional[CoerceIssue]]:
    """Attempt to coerce *raw* to *target* type.

    Returns ``(coerced_value, None)`` on success or
    ``(fallback, CoerceIssue)`` on failure.
    """
    try:
        if target == "int":
            return int(raw), None
        if target == "float":
            return float(raw), None
        if target == "bool":
            lower = raw.strip().lower()
            if lower in _BOOL_TRUE:
                return True, None
            if lower in _BOOL_FALSE:
                return False, None
            raise ValueError(f"unrecognised boolean literal {raw!r}")
        if target == "str":
            return raw, None
        raise CoerceError(f"unsupported target type {target!r}; choose from {_SUPPORTED}")
    except (ValueError, TypeError) as exc:
        fallback = default if default is not None else raw
        issue = CoerceIssue(key=key, raw_value=raw, target_type=target, reason=str(exc))
        return fallback, issue


def coerce(
    env: Dict[str, str],
    schema: Dict[str, str],
    defaults: Optional[Dict[str, str]] = None,
) -> CoerceResult:
    """Coerce *env* values according to *schema* ``{key: type}`` mapping.

    Keys absent from *schema* are left as strings.  *defaults* provides
    per-key fallback values used when coercion fails.
    """
    if defaults is None:
        defaults = {}

    result_env: Dict[str, Any] = {}
    issues: List[CoerceIssue] = []
    coerced_keys: List[str] = []

    for key, raw in env.items():
        target = schema.get(key)
        if target is None:
            result_env[key] = raw
            continue
        if target not in _SUPPORTED:
            raise CoerceError(
                f"unsupported target type {target!r} for key {key!r}; "
                f"choose from {_SUPPORTED}"
            )
        value, issue = _coerce_one(key, raw, target, defaults.get(key))
        result_env[key] = value
        if issue:
            issues.append(issue)
        else:
            coerced_keys.append(key)

    return CoerceResult(env=result_env, issues=issues, coerced_keys=coerced_keys)
