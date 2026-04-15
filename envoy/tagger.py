"""Tag env keys with arbitrary labels for grouping and filtering."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


class TagError(Exception):
    """Raised when tagging operations fail."""


@dataclass
class TagResult:
    """Result of a tagging operation."""

    env: Dict[str, str]
    tags: Dict[str, Set[str]]  # key -> set of tag labels
    tag_index: Dict[str, List[str]] = field(default_factory=dict)  # tag -> list of keys

    def has_tag(self, key: str, tag: str) -> bool:
        return tag in self.tags.get(key, set())

    def keys_for_tag(self, tag: str) -> List[str]:
        return self.tag_index.get(tag, [])

    def tags_for_key(self, key: str) -> Set[str]:
        return self.tags.get(key, set())

    def all_tags(self) -> Set[str]:
        result: Set[str] = set()
        for labels in self.tags.values():
            result |= labels
        return result

    def summary(self) -> str:
        total_keys = len(self.tags)
        total_tags = len(self.all_tags())
        return f"{total_keys} key(s) tagged across {total_tags} unique tag(s)."


def tag(
    env: Dict[str, str],
    tag_map: Dict[str, List[str]],
    *,
    ignore_missing: bool = True,
) -> TagResult:
    """Apply tags to env keys.

    Args:
        env: The environment dict to tag.
        tag_map: Mapping of key -> list of tag labels to apply.
        ignore_missing: If True, silently skip keys not in env.
                        If False, raise TagError for missing keys.

    Returns:
        TagResult with per-key tag sets and an inverted tag index.
    """
    tags: Dict[str, Set[str]] = {}
    tag_index: Dict[str, List[str]] = {}

    for key, labels in tag_map.items():
        if key not in env:
            if ignore_missing:
                continue
            raise TagError(f"Key '{key}' not found in env.")
        tags[key] = set(labels)
        for label in labels:
            tag_index.setdefault(label, []).append(key)

    return TagResult(env=env, tags=tags, tag_index=tag_index)
