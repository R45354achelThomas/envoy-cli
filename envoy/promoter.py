"""Promote env vars from one environment file to another, with conflict detection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class PromoteError(Exception):
    """Raised when promotion cannot be completed."""


@dataclass
class PromoteResult:
    source_path: str
    target_path: str
    promoted: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    conflicts: Dict[str, tuple] = field(default_factory=dict)  # key -> (src_val, tgt_val)

    def has_conflicts(self) -> bool:
        return bool(self.conflicts)

    def has_changes(self) -> bool:
        return bool(self.promoted)

    def summary(self) -> str:
        parts = [f"promoted={len(self.promoted)}", f"skipped={len(self.skipped)}",
                 f"conflicts={len(self.conflicts)}"]
        return ", ".join(parts)


def promote(
    source: Dict[str, str],
    target: Dict[str, str],
    keys: Optional[List[str]] = None,
    overwrite: bool = False,
    source_path: str = "<source>",
    target_path: str = "<target>",
) -> PromoteResult:
    """Promote selected (or all) keys from *source* into *target*.

    Args:
        source: Parsed env dict to promote from.
        target: Parsed env dict to promote into.
        keys: Explicit list of keys to promote; if None, all source keys are used.
        overwrite: When True, overwrite conflicting keys in target.
        source_path: Label used in the result for the source file.
        target_path: Label used in the result for the target file.

    Returns:
        PromoteResult describing what was promoted, skipped, and conflicted.
    """
    result = PromoteResult(source_path=source_path, target_path=target_path)
    candidates = keys if keys is not None else list(source.keys())

    merged = dict(target)

    for key in candidates:
        if key not in source:
            result.skipped.append(key)
            continue

        src_val = source[key]

        if key in target and target[key] != src_val:
            if overwrite:
                result.conflicts[key] = (src_val, target[key])
                merged[key] = src_val
                result.promoted[key] = src_val
            else:
                result.conflicts[key] = (src_val, target[key])
                # do NOT overwrite; leave target value intact
        else:
            merged[key] = src_val
            result.promoted[key] = src_val

    return result
