"""Duplicate an .env file to a new target, optionally filtering or transforming keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.parser import EnvParser


class DuplicateError(Exception):
    pass


@dataclass
class DuplicateResult:
    source_path: str
    target_path: str
    included_keys: List[str] = field(default_factory=list)
    excluded_keys: List[str] = field(default_factory=list)
    renamed_keys: Dict[str, str] = field(default_factory=dict)  # old -> new

    def has_changes(self) -> bool:
        return bool(self.excluded_keys or self.renamed_keys)

    def summary(self) -> str:
        parts = [f"Duplicated {len(self.included_keys)} key(s) from '{self.source_path}' to '{self.target_path}'."]
        if self.excluded_keys:
            parts.append(f"Excluded: {', '.join(sorted(self.excluded_keys))}.")
        if self.renamed_keys:
            renames = ", ".join(f"{old}->{new}" for old, new in sorted(self.renamed_keys.items()))
            parts.append(f"Renamed: {renames}.")
        return " ".join(parts)


def duplicate(
    env: Dict[str, str],
    source_path: str,
    target_path: str,
    exclude: Optional[List[str]] = None,
    rename: Optional[Dict[str, str]] = None,
) -> DuplicateResult:
    """Produce a new env dict suitable for writing to *target_path*.

    Args:
        env: Parsed key/value pairs from the source file.
        source_path: Original file path (used in result metadata only).
        target_path: Destination file path (used in result metadata only).
        exclude: Keys to omit from the output.
        rename: Mapping of {old_key: new_key} to apply before writing.

    Returns:
        DuplicateResult whose `.included_keys` reflects the final output.
    """
    exclude_set = set(exclude or [])
    rename_map = dict(rename or {})

    result = DuplicateResult(source_path=source_path, target_path=target_path)
    output: Dict[str, str] = {}

    for key, value in env.items():
        if key in exclude_set:
            result.excluded_keys.append(key)
            continue
        new_key = rename_map.get(key, key)
        if new_key != key:
            result.renamed_keys[key] = new_key
        output[new_key] = value
        result.included_keys.append(new_key)

    # Validate no rename target collides with an existing key that was kept
    seen: Dict[str, str] = {}
    for k in result.included_keys:
        if k in seen:
            raise DuplicateError(f"Duplicate output key '{k}' produced by rename/exclude rules.")
        seen[k] = k

    return result, output
