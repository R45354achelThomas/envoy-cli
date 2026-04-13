"""Resolve environment variables from multiple .env files with precedence rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from envoy.parser import EnvParser


class ResolveError(Exception):
    """Raised when resolution fails."""


@dataclass
class ResolvedEnv:
    """Result of resolving variables from multiple sources."""

    values: Dict[str, str] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)  # key -> source file
    overrides: Dict[str, List[Tuple[str, str]]] = field(default_factory=dict)  # key -> [(file, value)]

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        return self.values.get(key, default)

    def source_of(self, key: str) -> Optional[str]:
        """Return the file that provided the winning value for *key*."""
        return self.sources.get(key)

    def was_overridden(self, key: str) -> bool:
        """Return True if *key* appeared in more than one source file."""
        return len(self.overrides.get(key, [])) > 1

    def summary(self) -> str:
        lines = [f"Resolved {len(self.values)} variable(s) from {len(set(self.sources.values()))} file(s)."]
        overridden = [k for k in self.overrides if len(self.overrides[k]) > 1]
        if overridden:
            lines.append(f"Overridden keys ({len(overridden)}): {', '.join(sorted(overridden))}")
        return "\n".join(lines)


def resolve(file_paths: List[str], *, last_wins: bool = True) -> ResolvedEnv:
    """Load and merge variables from *file_paths* in order.

    Parameters
    ----------
    file_paths:
        Ordered list of .env file paths.  Earlier files have lower precedence
        when *last_wins* is True (the default), higher precedence otherwise.
    last_wins:
        When True the last file that defines a key wins.  When False the first
        definition wins and subsequent files cannot override it.
    """
    if not file_paths:
        raise ResolveError("At least one file path is required.")

    result = ResolvedEnv()
    parser = EnvParser()

    for path in file_paths:
        try:
            pairs = parser.parse_file(path)
        except Exception as exc:
            raise ResolveError(f"Failed to parse '{path}': {exc}") from exc

        for key, value in pairs.items():
            # Track every occurrence for auditing purposes
            result.overrides.setdefault(key, []).append((path, value))

            if key not in result.values:
                result.values[key] = value
                result.sources[key] = path
            elif last_wins:
                result.values[key] = value
                result.sources[key] = path
            # else: first_wins — keep existing value

    return result
