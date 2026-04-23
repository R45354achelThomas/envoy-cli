"""Mask sensitive values in an env dict, replacing them with a placeholder."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

_SECRET_PATTERNS = (
    "secret", "password", "passwd", "token", "api_key", "apikey",
    "auth", "private", "credential", "cert", "private_key",
)

DEFAULT_PLACEHOLDER = "***"


class MaskError(Exception):
    """Raised when masking fails."""


@dataclass
class MaskResult:
    masked: Dict[str, str]
    masked_keys: List[str] = field(default_factory=list)
    placeholder: str = DEFAULT_PLACEHOLDER

    def has_masked(self) -> bool:
        return bool(self.masked_keys)

    def summary(self) -> str:
        total = len(self.masked)
        n = len(self.masked_keys)
        return f"{n} of {total} key(s) masked with '{self.placeholder}'"


def _is_sensitive(key: str) -> bool:
    lower = key.lower()
    return any(pat in lower for pat in _SECRET_PATTERNS)


def mask(
    env: Dict[str, str],
    *,
    keys: Optional[List[str]] = None,
    placeholder: str = DEFAULT_PLACEHOLDER,
    auto_detect: bool = True,
) -> MaskResult:
    """Return a copy of *env* with sensitive values replaced by *placeholder*.

    Args:
        env: The source environment dict.
        keys: Explicit list of keys to mask (in addition to auto-detected ones).
        placeholder: The string to substitute for masked values.
        auto_detect: When True, keys matching known secret patterns are masked
            automatically even if not listed in *keys*.
    """
    if placeholder == "":
        raise MaskError("placeholder must not be empty")

    explicit = set(keys or [])
    result: Dict[str, str] = {}
    masked_keys: List[str] = []

    for k, v in env.items():
        if k in explicit or (auto_detect and _is_sensitive(k)):
            result[k] = placeholder
            masked_keys.append(k)
        else:
            result[k] = v

    return MaskResult(
        masked=result,
        masked_keys=sorted(masked_keys),
        placeholder=placeholder,
    )
