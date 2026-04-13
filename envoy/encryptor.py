"""Simple symmetric encryption helpers for .env secret values.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the *cryptography* package.
A passphrase is stretched with PBKDF2-HMAC-SHA256 so that a human-readable
password can be used directly without pre-generating a key.
"""

from __future__ import annotations

import base64
import os
from typing import Dict

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "envoy encryptor requires 'cryptography'. "
        "Install it with: pip install cryptography"
    ) from exc

_ITERATIONS = 390_000
_SALT_SIZE = 16


class EncryptionError(Exception):  # noqa: N818
    """Raised when encryption or decryption fails."""


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def encrypt_value(value: str, passphrase: str) -> str:
    """Return a base64-encoded ciphertext string prefixed with the salt."""
    salt = os.urandom(_SALT_SIZE)
    key = _derive_key(passphrase, salt)
    token = Fernet(key).encrypt(value.encode())
    # Store salt + token together, both base64-safe
    combined = base64.urlsafe_b64encode(salt) + b":" + token
    return combined.decode()


def decrypt_value(ciphertext: str, passphrase: str) -> str:
    """Decrypt a value previously encrypted with *encrypt_value*."""
    try:
        salt_b64, token = ciphertext.encode().split(b":", 1)
        salt = base64.urlsafe_b64decode(salt_b64)
        key = _derive_key(passphrase, salt)
        return Fernet(key).decrypt(token).decode()
    except (InvalidToken, ValueError, Exception) as exc:
        raise EncryptionError(f"Decryption failed: {exc}") from exc


def encrypt_dict(env: Dict[str, str], passphrase: str, keys: list[str] | None = None) -> Dict[str, str]:
    """Return a copy of *env* with selected (or all) values encrypted."""
    target_keys = set(keys) if keys is not None else set(env)
    return {
        k: encrypt_value(v, passphrase) if k in target_keys else v
        for k, v in env.items()
    }


def decrypt_dict(env: Dict[str, str], passphrase: str, keys: list[str] | None = None) -> Dict[str, str]:
    """Return a copy of *env* with selected (or all) values decrypted."""
    target_keys = set(keys) if keys is not None else set(env)
    return {
        k: decrypt_value(v, passphrase) if k in target_keys else v
        for k, v in env.items()
    }
