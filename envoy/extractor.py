"""Extract a subset of keys from an env dict into a new dict."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class ExtractError(Exception):
    """Raised when extraction cannot be completed."""


@dataclass
class ExtractResult:
    extracted: Dict[str, str]
    missing: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)

    def has_missing(self) -> bool:
        return bool(self.missing)

    def summary(self) -> str:
        parts = [f"extracted={len(self.extracted)}"]
        if self.missing:
            parts.append(f"missing={len(self.missing)}")
        if self.skipped:
            parts.append(f"skipped={len(self.skipped)}")
        return ", ".join(parts)


def extract(
    env: Dict[str, str],
    keys: List[str],
    *,
    allow_missing: bool = False,
    default: Optional[str] = None,
) -> ExtractResult:
    """Extract *keys* from *env*.

    Parameters
    ----------
    env:           Source env dict.
    keys:          Keys to extract.
    allow_missing: When True, absent keys are recorded but not fatal.
                   When False (default), an ExtractError is raised.
    default:       If given, absent keys receive this value (implies allow_missing).
    """
    if default is not None:
        allow_missing = True

    extracted: Dict[str, str] = {}
    missing: List[str] = []
    skipped: List[str] = []

    for key in keys:
        if key in env:
            extracted[key] = env[key]
        elif default is not None:
            extracted[key] = default
            missing.append(key)
        elif allow_missing:
            missing.append(key)
            skipped.append(key)
        else:
            raise ExtractError(f"Key not found in env: {key!r}")

    return ExtractResult(extracted=extracted, missing=missing, skipped=skipped)
