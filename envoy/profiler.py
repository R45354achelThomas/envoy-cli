"""Profile management: load and compare .env files against named profiles."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


class ProfileError(Exception):
    """Raised when a profile operation fails."""


@dataclass
class ProfileEntry:
    key: str
    expected: Optional[str]
    actual: Optional[str]

    @property
    def matches(self) -> bool:
        return self.expected == self.actual

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
            "matches": self.matches,
        }


@dataclass
class ProfileResult:
    profile_name: str
    entries: List[ProfileEntry] = field(default_factory=list)

    @property
    def is_compliant(self) -> bool:
        return all(e.matches for e in self.entries)

    @property
    def mismatches(self) -> List[ProfileEntry]:
        return [e for e in self.entries if not e.matches]

    def summary(self) -> str:
        total = len(self.entries)
        bad = len(self.mismatches)
        status = "COMPLIANT" if self.is_compliant else f"NON-COMPLIANT ({bad}/{total} mismatches)"
        return f"Profile '{self.profile_name}': {status}"


def load_profile(profile_path: str | Path) -> Dict[str, Optional[str]]:
    """Load a JSON profile file mapping keys to expected values (None = key must exist, any value)."""
    path = Path(profile_path)
    if not path.exists():
        raise ProfileError(f"Profile file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ProfileError(f"Invalid JSON in profile '{path}': {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError(f"Profile must be a JSON object, got {type(data).__name__}")
    return data


def check_profile(
    env: Dict[str, str],
    profile: Dict[str, Optional[str]],
    profile_name: str = "unnamed",
) -> ProfileResult:
    """Compare an env dict against a profile and return a ProfileResult."""
    entries: List[ProfileEntry] = []
    for key, expected in profile.items():
        actual = env.get(key)  # None if missing
        if expected is None:
            # Only presence matters; treat as match if key exists
            effective_expected = actual  # mirrors actual so it always matches when present
            if key not in env:
                effective_expected = "<any>"  # force mismatch
                actual = None
            entries.append(ProfileEntry(key=key, expected=effective_expected, actual=actual))
        else:
            entries.append(ProfileEntry(key=key, expected=expected, actual=actual))
    return ProfileResult(profile_name=profile_name, entries=entries)
