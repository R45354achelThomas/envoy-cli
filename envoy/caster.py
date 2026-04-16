"""Type-casting for .env values."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List


class CastError(Exception):
    pass


@dataclass
class CastResult:
    casted: Dict[str, Any] = field(default_factory=dict)
    failed: Dict[str, str] = field(default_factory=dict)

    def has_failures(self) -> bool:
        return bool(self.failed)

    def summary(self) -> str:
        ok = len(self.casted)
        bad = len(self.failed)
        return f"{ok} key(s) cast successfully, {bad} failure(s)"


_BOOL_TRUE = {"true", "1", "yes", "on"}
_BOOL_FALSE = {"false", "0", "no", "off"}


def _cast_one(value: str, typ: str) -> Any:
    if typ == "int":
        try:
            return int(value)
        except ValueError:
            raise CastError(f"Cannot cast {value!r} to int")
    if typ == "float":
        try:
            return float(value)
        except ValueError:
            raise CastError(f"Cannot cast {value!r} to float")
    if typ == "bool":
        low = value.lower()
        if low in _BOOL_TRUE:
            return True
        if low in _BOOL_FALSE:
            return False
        raise CastError(f"Cannot cast {value!r} to bool")
    if typ == "list":
        return [item.strip() for item in value.split(",") if item.strip()]
    if typ == "str":
        return value
    raise CastError(f"Unknown type {typ!r}")


def cast(env: Dict[str, str], schema: Dict[str, str]) -> CastResult:
    """Cast env values according to schema mapping key -> type."""
    result = CastResult()
    for key, value in env.items():
        typ = schema.get(key, "str")
        try:
            result.casted[key] = _cast_one(value, typ)
        except CastError as exc:
            result.failed[key] = str(exc)
            result.casted[key] = value  # keep original on failure
    return result
