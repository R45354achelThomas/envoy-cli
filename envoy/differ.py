"""Key-level differ: compare two env dicts and produce a structured report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class DifferError(Exception):
    """Raised when the differ encounters an unrecoverable problem."""


@dataclass
class DiffRecord:
    key: str
    status: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def __str__(self) -> str:
        if self.status == "added":
            return f"+ {self.key}={self.new_value!r}"
        if self.status == "removed":
            return f"- {self.key}={self.old_value!r}"
        if self.status == "changed":
            return f"~ {self.key}: {self.old_value!r} -> {self.new_value!r}"
        return f"  {self.key}={self.new_value!r}"


@dataclass
class DifferResult:
    records: List[DiffRecord] = field(default_factory=list)

    @property
    def added(self) -> List[DiffRecord]:
        return [r for r in self.records if r.status == "added"]

    @property
    def removed(self) -> List[DiffRecord]:
        return [r for r in self.records if r.status == "removed"]

    @property
    def changed(self) -> List[DiffRecord]:
        return [r for r in self.records if r.status == "changed"]

    @property
    def unchanged(self) -> List[DiffRecord]:
        return [r for r in self.records if r.status == "unchanged"]

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.removed:
            parts.append(f"{len(self.removed)} removed")
        if self.changed:
            parts.append(f"{len(self.changed)} changed")
        if not parts:
            return "No differences found."
        return ", ".join(parts) + "."


def differ(
    old: Dict[str, str],
    new: Dict[str, str],
    *,
    include_unchanged: bool = False,
) -> DifferResult:
    """Compare *old* and *new* env dicts and return a :class:`DifferResult`."""
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise DifferError("Both arguments must be dicts.")

    records: List[DiffRecord] = []
    all_keys = sorted(set(old) | set(new))

    for key in all_keys:
        in_old = key in old
        in_new = key in new
        if in_old and not in_new:
            records.append(DiffRecord(key, "removed", old_value=old[key]))
        elif in_new and not in_old:
            records.append(DiffRecord(key, "added", new_value=new[key]))
        elif old[key] != new[key]:
            records.append(DiffRecord(key, "changed", old_value=old[key], new_value=new[key]))
        elif include_unchanged:
            records.append(DiffRecord(key, "unchanged", old_value=old[key], new_value=new[key]))

    return DifferResult(records=records)
