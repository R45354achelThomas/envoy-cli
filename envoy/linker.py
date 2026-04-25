"""Link (cross-reference) keys across multiple .env files, reporting shared and unique keys."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set


class LinkError(Exception):
    """Raised when linking fails."""


@dataclass
class LinkResult:
    """Result of linking multiple env files."""

    sources: List[str]  # ordered file labels / paths
    shared: Dict[str, List[str]]  # key -> list of sources that define it
    unique: Dict[str, str]  # key -> single source that defines it
    all_keys: Set[str] = field(default_factory=set)

    def has_shared(self) -> bool:
        return bool(self.shared)

    def has_unique(self) -> bool:
        return bool(self.unique)

    def sources_for(self, key: str) -> List[str]:
        """Return all sources that define *key*."""
        if key in self.shared:
            return self.shared[key]
        if key in self.unique:
            return [self.unique[key]]
        return []

    def summary(self) -> str:
        lines = [
            f"Sources  : {len(self.sources)}",
            f"Total keys: {len(self.all_keys)}",
            f"Shared   : {len(self.shared)}",
            f"Unique   : {len(self.unique)}",
        ]
        return "\n".join(lines)


def link(envs: Dict[str, Dict[str, str]]) -> LinkResult:
    """Cross-reference *envs*, a mapping of label -> parsed env dict.

    Args:
        envs: ordered dict of {label: {KEY: value}}.

    Returns:
        LinkResult describing shared and unique keys.
    """
    if not envs:
        raise LinkError("At least one environment must be provided.")

    sources = list(envs.keys())
    key_sources: Dict[str, List[str]] = {}

    for label, env in envs.items():
        for key in env:
            key_sources.setdefault(key, []).append(label)

    shared: Dict[str, List[str]] = {
        k: v for k, v in key_sources.items() if len(v) > 1
    }
    unique: Dict[str, str] = {
        k: v[0] for k, v in key_sources.items() if len(v) == 1
    }
    all_keys: Set[str] = set(key_sources.keys())

    return LinkResult(sources=sources, shared=shared, unique=unique, all_keys=all_keys)
