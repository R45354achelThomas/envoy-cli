"""Sort keys in a .env file alphabetically or by custom group order."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class SortError(Exception):
    """Raised when sorting cannot be completed."""


@dataclass
class SortResult:
    original: Dict[str, str]
    sorted_env: Dict[str, str]
    order: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return list(self.original.keys()) != list(self.sorted_env.keys())

    def summary(self) -> str:
        if not self.has_changes:
            return "Already sorted — no changes made."
        return f"Sorted {len(self.sorted_env)} keys."

    def to_dotenv(self) -> str:
        lines = []
        for key, value in self.sorted_env.items():
            if " " in value or "#" in value:
                lines.append(f'{key}="{value}"')
            else:
                lines.append(f"{key}={value}")
        return "\n".join(lines) + ("\n" if lines else "")


def sort(
    env: Dict[str, str],
    groups: Optional[List[List[str]]] = None,
    case_sensitive: bool = False,
) -> SortResult:
    """Sort *env* keys.

    Parameters
    ----------
    env:
        Parsed key/value mapping.
    groups:
        Optional list of key-group lists.  Keys within each group are sorted
        together and the groups maintain their relative order.  Keys not
        mentioned in any group are appended alphabetically at the end.
    case_sensitive:
        When *False* (default) sorting ignores case.
    """
    if not isinstance(env, dict):
        raise SortError("env must be a dict")

    key_fn = (lambda k: k) if case_sensitive else (lambda k: k.lower())

    if groups is None:
        ordered_keys = sorted(env.keys(), key=key_fn)
    else:
        seen: set[str] = set()
        ordered_keys: List[str] = []
        for group in groups:
            members = [k for k in group if k in env]
            members.sort(key=key_fn)
            for k in members:
                if k not in seen:
                    ordered_keys.append(k)
                    seen.add(k)
        # append remaining keys not covered by any group
        remaining = sorted((k for k in env if k not in seen), key=key_fn)
        ordered_keys.extend(remaining)

    sorted_env = {k: env[k] for k in ordered_keys}
    return SortResult(original=dict(env), sorted_env=sorted_env, order=ordered_keys)
