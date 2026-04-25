"""Type-check .env values against a schema of expected types."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

_SUPPORTED_TYPES = {"str", "int", "float", "bool"}
_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}


class TypeCheckError(Exception):
    """Raised for configuration or fatal errors."""


@dataclass
class TypeIssue:
    key: str
    expected: str
    actual_value: str
    message: str

    def __str__(self) -> str:
        return f"{self.key}: expected {self.expected}, got {self.actual_value!r} — {self.message}"


@dataclass
class TypeCheckResult:
    env: Dict[str, Any]
    issues: List[TypeIssue] = field(default_factory=list)

    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        if not self.issues:
            return "All values match their expected types."
        return f"{len(self.issues)} type mismatch(es) found."


def _try_cast(value: str, expected: str) -> tuple[bool, Any, str]:
    """Return (ok, cast_value, error_message)."""
    if expected == "str":
        return True, value, ""
    if expected == "int":
        try:
            return True, int(value), ""
        except ValueError:
            return False, value, f"cannot convert to int"
    if expected == "float":
        try:
            return True, float(value), ""
        except ValueError:
            return False, value, f"cannot convert to float"
    if expected == "bool":
        lower = value.lower()
        if lower in _BOOL_TRUE:
            return True, True, ""
        if lower in _BOOL_FALSE:
            return True, False, ""
        return False, value, f"expected a boolean-like value (true/false/yes/no/1/0)"
    return False, value, f"unsupported type '{expected}'"


def typecheck(env: Dict[str, str], schema: Dict[str, str]) -> TypeCheckResult:
    """Validate and cast *env* values according to *schema* type annotations.

    Args:
        env: Parsed key/value mapping.
        schema: Mapping of key -> expected type string (str/int/float/bool).

    Returns:
        TypeCheckResult with cast values for valid keys and issues for failures.
    """
    for expected_type in schema.values():
        if expected_type not in _SUPPORTED_TYPES:
            raise TypeCheckError(f"Unsupported type in schema: '{expected_type}'")

    cast_env: Dict[str, Any] = {}
    issues: List[TypeIssue] = []

    for key, value in env.items():
        expected = schema.get(key, "str")
        ok, cast_value, msg = _try_cast(value, expected)
        if ok:
            cast_env[key] = cast_value
        else:
            issues.append(TypeIssue(key=key, expected=expected, actual_value=value, message=msg))
            cast_env[key] = value  # keep original on failure

    return TypeCheckResult(env=cast_env, issues=issues)
