"""Tests for envoy.encryptor."""

import pytest

from envoy.encryptor import (
    EncryptionError,
    decrypt_dict,
    decrypt_value,
    encrypt_dict,
    encrypt_value,
)

PASS = "correct-horse-battery-staple"


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

def test_encrypt_decrypt_roundtrip():
    plaintext = "super-secret-value"
    ciphertext = encrypt_value(plaintext, PASS)
    assert decrypt_value(ciphertext, PASS) == plaintext


def test_ciphertext_differs_from_plaintext():
    plaintext = "my_password"
    ciphertext = encrypt_value(plaintext, PASS)
    assert ciphertext != plaintext


def test_two_encryptions_produce_different_ciphertext():
    """Fernet uses a random IV, so two encryptions must differ."""
    v1 = encrypt_value("same", PASS)
    v2 = encrypt_value("same", PASS)
    assert v1 != v2


def test_wrong_passphrase_raises_encryption_error():
    ciphertext = encrypt_value("secret", PASS)
    with pytest.raises(EncryptionError):
        decrypt_value(ciphertext, "wrong-passphrase")


def test_corrupted_ciphertext_raises_encryption_error():
    ciphertext = encrypt_value("secret", PASS)
    corrupted = ciphertext[:-4] + "XXXX"
    with pytest.raises(EncryptionError):
        decrypt_value(corrupted, PASS)


def test_empty_string_roundtrip():
    assert decrypt_value(encrypt_value("", PASS), PASS) == ""


# ---------------------------------------------------------------------------
# Dict helpers
# ---------------------------------------------------------------------------

def test_encrypt_dict_all_values():
    env = {"DB_PASS": "secret", "HOST": "localhost"}
    encrypted = encrypt_dict(env, PASS)
    assert encrypted["DB_PASS"] != "secret"
    assert encrypted["HOST"] != "localhost"


def test_encrypt_dict_selected_keys_only():
    env = {"DB_PASS": "secret", "HOST": "localhost"}
    encrypted = encrypt_dict(env, PASS, keys=["DB_PASS"])
    assert encrypted["DB_PASS"] != "secret"
    assert encrypted["HOST"] == "localhost"  # untouched


def test_decrypt_dict_roundtrip():
    env = {"DB_PASS": "secret", "API_KEY": "abc123"}
    encrypted = encrypt_dict(env, PASS)
    decrypted = decrypt_dict(encrypted, PASS)
    assert decrypted == env


def test_decrypt_dict_selected_keys_only():
    env = {"DB_PASS": "secret", "HOST": "localhost"}
    encrypted = encrypt_dict(env, PASS, keys=["DB_PASS"])
    decrypted = decrypt_dict(encrypted, PASS, keys=["DB_PASS"])
    assert decrypted == env


def test_encrypt_dict_preserves_key_order():
    env = {"Z": "last", "A": "first", "M": "middle"}
    encrypted = encrypt_dict(env, PASS)
    assert list(encrypted.keys()) == list(env.keys())
