"""Group env keys by prefix or custom mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class GroupError(Exception):
    pass


@dataclass
class GroupResult:
    groups: Dict[str, Dict[str, str]] = field(default_factory=dict)
    ungrouped: Dict[str, str] = field(default_factory=dict)

    def has_ungrouped(self) -> bool:
        return bool(self.ungrouped)

    def group_names(self) -> List[str]:
        return sorted(self.groups.keys())

    def summary(self) -> str:
        parts = [f"{name}: {len(keys)} key(s)" for name, keys in sorted(self.groups.items())]
        if self.ungrouped:
            parts.append(f"(ungrouped): {len(self.ungrouped)} key(s)")
        return ", ".join(parts) if parts else "no keys"


def group(
    env: Dict[str, str],
    *,
    separator: str = "_",
    prefix_map: Optional[Dict[str, str]] = None,
    min_prefix_length: int = 2,
) -> GroupResult:
    """Group env keys by their prefix.

    If *prefix_map* is provided it maps prefixes (upper-cased) to group names.
    Otherwise the first segment split by *separator* is used as the group name.
    Keys whose prefix is shorter than *min_prefix_length* land in *ungrouped*.
    """
    if not isinstance(env, dict):
        raise GroupError("env must be a dict")

    result = GroupResult()

    for key, value in env.items():
        group_name = _resolve_group(
            key,
            separator=separator,
            prefix_map=prefix_map,
            min_prefix_length=min_prefix_length,
        )
        if group_name is None:
            result.ungrouped[key] = value
        else:
            result.groups.setdefault(group_name, {})[key] = value

    return result


def _resolve_group(
    key: str,
    *,
    separator: str,
    prefix_map: Optional[Dict[str, str]],
    min_prefix_length: int,
) -> Optional[str]:
    if prefix_map:
        upper = key.upper()
        for prefix, name in prefix_map.items():
            if upper.startswith(prefix.upper()):
                return name
        return None

    parts = key.split(separator, 1)
    if len(parts) < 2 or len(parts[0]) < min_prefix_length:
        return None
    return parts[0].upper()
