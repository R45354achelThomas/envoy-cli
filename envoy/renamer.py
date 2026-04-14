"""Rename keys across a parsed .env mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


class RenameError(Exception):
    """Raised when a rename operation cannot be completed."""


@dataclass
class RenameResult:
    """Outcome of a bulk rename operation."""

    renamed: List[Tuple[str, str]] = field(default_factory=list)   # (old, new)
    skipped: List[Tuple[str, str]] = field(default_factory=list)   # (old, reason)
    env: Dict[str, str] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.renamed)

    def summary(self) -> str:
        parts = [f"{len(self.renamed)} key(s) renamed"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        return ", ".join(parts) + "."


def rename(
    env: Dict[str, str],
    renames: Dict[str, str],
    *,
    allow_overwrite: bool = False,
) -> RenameResult:
    """Return a new env dict with keys renamed according to *renames*.

    Parameters
    ----------
    env:
        Source key/value mapping.
    renames:
        Mapping of ``{old_key: new_key}``.
    allow_overwrite:
        When *False* (default) a rename that would clobber an existing key is
        skipped and recorded in ``RenameResult.skipped``.
    """
    if not isinstance(renames, dict):
        raise RenameError("renames must be a dict mapping old keys to new keys")

    result_env: Dict[str, str] = dict(env)
    renamed: List[Tuple[str, str]] = []
    skipped: List[Tuple[str, str]] = []

    for old_key, new_key in renames.items():
        if not isinstance(old_key, str) or not isinstance(new_key, str):
            raise RenameError(
                f"Both old and new key names must be strings, got {old_key!r} -> {new_key!r}"
            )
        if old_key not in result_env:
            skipped.append((old_key, "key not found"))
            continue
        if new_key == old_key:
            skipped.append((old_key, "old and new names are identical"))
            continue
        if new_key in result_env and not allow_overwrite:
            skipped.append((old_key, f"target key '{new_key}' already exists"))
            continue

        result_env[new_key] = result_env.pop(old_key)
        renamed.append((old_key, new_key))

    return RenameResult(renamed=renamed, skipped=skipped, env=result_env)
