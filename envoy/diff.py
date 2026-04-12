"""Secret-aware diffing between two parsed .env dictionaries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

SECRET_PATTERNS = ("SECRET", "PASSWORD", "PASSWD", "TOKEN", "KEY", "PRIVATE", "CREDENTIAL")


def _is_secret(key: str) -> bool:
    upper = key.upper()
    return any(pattern in upper for pattern in SECRET_PATTERNS)


def _mask(value: str) -> str:
    if len(value) <= 4:
        return "****"
    return value[:2] + "*" * (len(value) - 4) + value[-2:]


@dataclass
class DiffEntry:
    key: str
    status: str          # 'added' | 'removed' | 'changed' | 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    is_secret: bool = False

    @property
    def display_old(self) -> Optional[str]:
        if self.is_secret and self.old_value is not None:
            return _mask(self.old_value)
        return self.old_value

    @property
    def display_new(self) -> Optional[str]:
        if self.is_secret and self.new_value is not None:
            return _mask(self.new_value)
        return self.new_value


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "changed"]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "unchanged"]

    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)


def diff_envs(
    base: Dict[str, str],
    target: Dict[str, str],
    show_unchanged: bool = False,
) -> DiffResult:
    """Compute the diff between two env dicts.

    Args:
        base: The reference environment (e.g. .env.staging).
        target: The environment to compare against (e.g. .env.production).
        show_unchanged: Include keys with identical values in the result.

    Returns:
        A DiffResult containing categorised DiffEntry objects.
    """
    result = DiffResult()
    all_keys = sorted(set(base) | set(target))
    for key in all_keys:
        secret = _is_secret(key)
        if key not in base:
            result.entries.append(DiffEntry(key, "added", new_value=target[key], is_secret=secret))
        elif key not in target:
            result.entries.append(DiffEntry(key, "removed", old_value=base[key], is_secret=secret))
        elif base[key] != target[key]:
            result.entries.append(
                DiffEntry(key, "changed", old_value=base[key], new_value=target[key], is_secret=secret)
            )
        elif show_unchanged:
            result.entries.append(
                DiffEntry(key, "unchanged", old_value=base[key], new_value=target[key], is_secret=secret)
            )
    return result
