"""Map (rename/transform) env keys using a mapping schema."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class MapError(Exception):
    """Raised when the mapper encounters an unrecoverable problem."""


@dataclass
class MapResult:
    env: Dict[str, str]
    mapped_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)
    dropped_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.mapped_keys or self.dropped_keys)

    def summary(self) -> str:
        parts = []
        if self.mapped_keys:
            parts.append(f"{len(self.mapped_keys)} key(s) mapped")
        if self.dropped_keys:
            parts.append(f"{len(self.dropped_keys)} key(s) dropped")
        if self.skipped_keys:
            parts.append(f"{len(self.skipped_keys)} key(s) skipped (not in mapping)")
        return ", ".join(parts) if parts else "no changes"


def map_env(
    env: Dict[str, str],
    mapping: Dict[str, Optional[str]],
    *,
    drop_unmapped: bool = False,
) -> MapResult:
    """Return a new env dict with keys renamed according to *mapping*.

    *mapping* values of ``None`` cause the key to be dropped entirely.
    If *drop_unmapped* is ``True``, keys absent from *mapping* are omitted.
    """
    if not isinstance(mapping, dict):
        raise MapError("mapping must be a dict")

    result: Dict[str, str] = {}
    mapped_keys: List[str] = []
    skipped_keys: List[str] = []
    dropped_keys: List[str] = []

    for old_key, value in env.items():
        if old_key in mapping:
            new_key = mapping[old_key]
            if new_key is None:
                dropped_keys.append(old_key)
            else:
                if new_key in result:
                    raise MapError(
                        f"mapping collision: multiple keys resolve to '{new_key}'"
                    )
                result[new_key] = value
                mapped_keys.append(old_key)
        else:
            if drop_unmapped:
                skipped_keys.append(old_key)
            else:
                if old_key in result:
                    raise MapError(
                        f"mapping collision: '{old_key}' already present in output"
                    )
                result[old_key] = value
                skipped_keys.append(old_key)

    return MapResult(
        env=result,
        mapped_keys=mapped_keys,
        skipped_keys=skipped_keys,
        dropped_keys=dropped_keys,
    )
