"""Pin environment variable values to a snapshot for drift detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class PinError(Exception):
    """Raised when a pinning operation fails."""


@dataclass
class PinResult:
    pinned: Dict[str, str]          # key -> pinned value
    drifted: List[str] = field(default_factory=list)   # keys whose values differ from pin
    missing: List[str] = field(default_factory=list)   # keys in pin but absent from env
    new_keys: List[str] = field(default_factory=list)  # keys in env but absent from pin

    def has_drift(self) -> bool:
        """Return True if any drift was detected."""
        return bool(self.drifted or self.missing)

    def summary(self) -> str:
        parts = [f"{len(self.pinned)} pinned"]
        if self.drifted:
            parts.append(f"{len(self.drifted)} drifted")
        if self.missing:
            parts.append(f"{len(self.missing)} missing")
        if self.new_keys:
            parts.append(f"{len(self.new_keys)} new")
        return ", ".join(parts)


def pin(
    env: Dict[str, str],
    existing_pin: Optional[Dict[str, str]] = None,
    keys: Optional[List[str]] = None,
) -> PinResult:
    """Create or compare a pin of *env*.

    If *existing_pin* is provided the result reports drift against it.
    If *keys* is provided only those keys are considered.
    """
    if keys is not None:
        unknown = [k for k in keys if k not in env]
        if unknown:
            raise PinError(f"Keys not found in env: {', '.join(sorted(unknown))}")
        target = {k: env[k] for k in keys}
    else:
        target = dict(env)

    if existing_pin is None:
        return PinResult(pinned=target)

    drifted = [k for k, v in existing_pin.items() if k in target and target[k] != v]
    missing = [k for k in existing_pin if k not in target]
    new_keys = [k for k in target if k not in existing_pin]

    return PinResult(
        pinned=existing_pin,
        drifted=drifted,
        missing=missing,
        new_keys=new_keys,
    )
