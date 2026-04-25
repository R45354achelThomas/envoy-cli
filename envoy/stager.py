"""Stage environment variables for promotion across environments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class StageError(Exception):
    """Raised when staging fails."""


@dataclass
class StageResult:
    staged: Dict[str, str]
    skipped: List[str]
    source_env: str
    target_env: str
    overwritten: List[str] = field(default_factory=list)

    def has_skipped(self) -> bool:
        return len(self.skipped) > 0

    def has_overwritten(self) -> bool:
        return len(self.overwritten) > 0

    def summary(self) -> str:
        parts = [
            f"Staged {len(self.staged)} key(s) from '{self.source_env}' to '{self.target_env}'.",
        ]
        if self.overwritten:
            parts.append(f"Overwrote {len(self.overwritten)} existing key(s): {', '.join(self.overwritten)}.")
        if self.skipped:
            parts.append(f"Skipped {len(self.skipped)} key(s): {', '.join(self.skipped)}.")
        return " ".join(parts)


def stage(
    source: Dict[str, str],
    target: Dict[str, str],
    keys: Optional[List[str]] = None,
    *,
    overwrite: bool = True,
    source_env: str = "source",
    target_env: str = "target",
) -> StageResult:
    """Stage keys from *source* into *target*.

    Args:
        source: The environment to pull values from.
        target: The environment to push values into.
        keys: Specific keys to stage; if None, all source keys are staged.
        overwrite: When False, existing keys in *target* are skipped.
        source_env: Label for the source environment (used in summary).
        target_env: Label for the target environment (used in summary).

    Returns:
        A :class:`StageResult` describing what happened.
    """
    candidates = list(keys) if keys is not None else list(source.keys())

    staged: Dict[str, str] = dict(target)
    staged_keys: Dict[str, str] = {}
    skipped: List[str] = []
    overwritten: List[str] = []

    for key in candidates:
        if key not in source:
            skipped.append(key)
            continue
        if key in target and not overwrite:
            skipped.append(key)
            continue
        if key in target and source[key] != target[key]:
            overwritten.append(key)
        staged[key] = source[key]
        staged_keys[key] = source[key]

    return StageResult(
        staged=staged,
        skipped=skipped,
        source_env=source_env,
        target_env=target_env,
        overwritten=overwritten,
    )
