"""Freeze a resolved .env into a single immutable snapshot dict.

A 'frozen' env captures the final resolved values (after interpolation)
along with a SHA-256 digest of the entire key-value set so callers can
detect tampering or unintentional drift.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, Optional


class FreezeError(Exception):
    """Raised when freezing or verification fails."""


@dataclass
class FreezeResult:
    env: Dict[str, str]
    digest: str
    key_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.key_count = len(self.env)

    def has_drift(self, other: "FreezeResult") -> bool:
        """Return True if *other* has a different digest."""
        return self.digest != other.digest

    def summary(self) -> str:
        return (
            f"{self.key_count} key(s) frozen  "
            f"[sha256:{self.digest[:12]}]"
        )

    def to_dict(self) -> dict:
        return {"env": self.env, "digest": self.digest}

    @classmethod
    def from_dict(cls, data: dict) -> "FreezeResult":
        env = data.get("env")
        if not isinstance(env, dict):
            raise FreezeError("Invalid freeze data: 'env' must be a mapping.")
        expected = _compute_digest(env)
        stored = data.get("digest", "")
        if stored != expected:
            raise FreezeError(
                f"Digest mismatch: stored={stored!r}  computed={expected!r}"
            )
        return cls(env=env, digest=expected)


def _compute_digest(env: Dict[str, str]) -> str:
    """Deterministic SHA-256 over sorted key=value pairs."""
    canonical = json.dumps(
        {k: env[k] for k in sorted(env)}, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def freeze(
    env: Dict[str, str],
    *,
    keys: Optional[list] = None,
) -> FreezeResult:
    """Freeze *env* (or a subset of *keys*) and return a FreezeResult.

    Parameters
    ----------
    env:  Mapping of resolved key-value pairs.
    keys: Optional explicit list of keys to include.  Unknown keys are
          silently skipped.  If *None*, all keys are included.
    """
    if keys is not None:
        subset = {k: env[k] for k in keys if k in env}
    else:
        subset = dict(env)

    digest = _compute_digest(subset)
    return FreezeResult(env=subset, digest=digest)
