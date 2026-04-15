"""Prefix/unprefixer: add or strip a prefix from all keys in an env mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


class PrefixError(Exception):
    """Raised when a prefix operation cannot be completed."""


@dataclass
class PrefixResult:
    env: Dict[str, str]
    changed_keys: List[str] = field(default_factory=list)
    skipped_keys: List[str] = field(default_factory=list)

    def has_changes(self) -> bool:
        return bool(self.changed_keys)

    def summary(self) -> str:
        parts = [f"{len(self.changed_keys)} key(s) transformed"]
        if self.skipped_keys:
            parts.append(f"{len(self.skipped_keys)} key(s) skipped")
        return ", ".join(parts)


def add_prefix(
    env: Dict[str, str],
    prefix: str,
    *,
    skip_existing: bool = True,
) -> PrefixResult:
    """Return a new env dict with *prefix* prepended to every key.

    If *skip_existing* is True (default) keys that already start with the
    prefix are left unchanged and recorded in ``skipped_keys``.
    """
    if not prefix:
        raise PrefixError("prefix must be a non-empty string")

    out: Dict[str, str] = {}
    changed: List[str] = []
    skipped: List[str] = []

    for key, value in env.items():
        if skip_existing and key.startswith(prefix):
            out[key] = value
            skipped.append(key)
        else:
            new_key = prefix + key
            out[new_key] = value
            changed.append(key)

    return PrefixResult(env=out, changed_keys=changed, skipped_keys=skipped)


def strip_prefix(
    env: Dict[str, str],
    prefix: str,
    *,
    skip_non_matching: bool = True,
) -> PrefixResult:
    """Return a new env dict with *prefix* removed from every key.

    If *skip_non_matching* is True (default) keys that do not start with
    the prefix are kept as-is and recorded in ``skipped_keys``.
    """
    if not prefix:
        raise PrefixError("prefix must be a non-empty string")

    out: Dict[str, str] = {}
    changed: List[str] = []
    skipped: List[str] = []

    for key, value in env.items():
        if key.startswith(prefix):
            new_key = key[len(prefix):]
            if not new_key:
                raise PrefixError(
                    f"stripping '{prefix}' from '{key}' would produce an empty key"
                )
            out[new_key] = value
            changed.append(key)
        elif skip_non_matching:
            out[key] = value
            skipped.append(key)
        else:
            raise PrefixError(
                f"key '{key}' does not start with prefix '{prefix}'"
            )

    return PrefixResult(env=out, changed_keys=changed, skipped_keys=skipped)
