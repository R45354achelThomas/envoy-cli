"""Merge multiple .env files with conflict detection and override support."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MergeConflict:
    key: str
    values: List[Tuple[str, str]]  # list of (source_name, value)

    def __str__(self) -> str:
        lines = [f"Conflict on key '{self.key}':"]
        for source, value in self.values:
            lines.append(f"  [{source}] {value}")
        return "\n".join(lines)


@dataclass
class MergeResult:
    merged: Dict[str, str] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        lines = [
            f"Merged {len(self.sources)} source(s): {', '.join(self.sources)}",
            f"Total keys: {len(self.merged)}",
        ]
        if self.conflicts:
            lines.append(f"Conflicts: {len(self.conflicts)}")
            for c in self.conflicts:
                lines.append(f"  - {c.key}")
        else:
            lines.append("No conflicts detected.")
        return "\n".join(lines)

    def conflict_keys(self) -> List[str]:
        """Return a sorted list of keys that have conflicts."""
        return sorted(c.key for c in self.conflicts)


def merge_envs(
    sources: List[Tuple[str, Dict[str, str]]],
    override: bool = False,
    ignore_conflicts: bool = False,
) -> MergeResult:
    """Merge multiple env dicts.

    Args:
        sources: List of (name, env_dict) tuples in priority order (last wins if override=True).
        override: If True, later sources silently override earlier ones.
        ignore_conflicts: If True, conflicts are not recorded (first value wins).

    Returns:
        MergeResult with merged env and any conflicts.
    """
    result = MergeResult(sources=[name for name, _ in sources])
    seen: Dict[str, Tuple[str, str]] = {}  # key -> (source_name, value)

    for source_name, env in sources:
        for key, value in env.items():
            if key not in seen:
                seen[key] = (source_name, value)
                result.merged[key] = value
            else:
                prev_source, prev_value = seen[key]
                if prev_value == value:
                    continue
                if override:
                    seen[key] = (source_name, value)
                    result.merged[key] = value
                elif not ignore_conflicts:
                    existing = next(
                        (c for c in result.conflicts if c.key == key), None
                    )
                    if existing is None:
                        result.conflicts.append(
                            MergeConflict(
                                key=key,
                                values=[(prev_source, prev_value), (source_name, value)],
                            )
                        )
                    else:
                        existing.values.append((source_name, value))

    return result
