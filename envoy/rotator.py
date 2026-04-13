"""Key rotation support: re-encrypt an env dict under a new passphrase."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy.encryptor import EncryptionError, decrypt_value, encrypt_value


class RotationError(Exception):
    """Raised when key rotation fails."""


@dataclass
class RotationResult:
    rotated: Dict[str, str] = field(default_factory=dict)
    skipped: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)

    @property
    def has_failures(self) -> bool:
        return bool(self.failed)

    def summary(self) -> str:
        parts = [f"{len(self.rotated)} key(s) rotated"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped (not encrypted)")
        if self.failed:
            parts.append(f"{len(self.failed)} failed")
        return ", ".join(parts)


def rotate(
    env: Dict[str, str],
    old_passphrase: str,
    new_passphrase: str,
    keys: Optional[List[str]] = None,
) -> RotationResult:
    """Re-encrypt values in *env* from *old_passphrase* to *new_passphrase*.

    If *keys* is provided, only those keys are considered; otherwise every
    key whose value starts with the ``enc:`` prefix is processed.

    Returns a :class:`RotationResult` with the updated mapping and metadata.
    Raises :class:`RotationError` if *env* is empty or *keys* contains entries
    not present in *env*.
    """
    if not isinstance(env, dict):
        raise RotationError("env must be a dict")

    candidates = keys if keys is not None else list(env.keys())

    missing = [k for k in candidates if k not in env]
    if missing:
        raise RotationError(f"Keys not found in env: {', '.join(missing)}")

    result = RotationResult(rotated=dict(env))

    for key in candidates:
        value = env[key]
        if not value.startswith("enc:"):
            result.skipped.append(key)
            continue
        try:
            plaintext = decrypt_value(value, old_passphrase)
            result.rotated[key] = encrypt_value(plaintext, new_passphrase)
        except EncryptionError:
            result.failed.append(key)
            # keep original value in rotated dict
            result.rotated[key] = value

    return result
