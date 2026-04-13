"""Tests for envoy.rotator."""

import pytest

from envoy.encryptor import decrypt_value, encrypt_value
from envoy.rotator import RotationError, RotationResult, rotate

OLD_PASS = "old-secret"
NEW_PASS = "new-secret"


def _enc(value: str, passphrase: str = OLD_PASS) -> str:
    return encrypt_value(value, passphrase)


# ---------------------------------------------------------------------------
# RotationResult helpers
# ---------------------------------------------------------------------------

def test_rotation_result_has_failures_false_when_empty():
    r = RotationResult(rotated={}, skipped=[], failed=[])
    assert not r.has_failures


def test_rotation_result_has_failures_true_when_failed():
    r = RotationResult(rotated={}, skipped=[], failed=["KEY"])
    assert r.has_failures


def test_rotation_result_summary_includes_counts():
    r = RotationResult(
        rotated={"A": "x", "B": "y"},
        skipped=["C"],
        failed=["D"],
    )
    summary = r.summary()
    assert "2" in summary
    assert "skipped" in summary
    assert "failed" in summary


# ---------------------------------------------------------------------------
# rotate()
# ---------------------------------------------------------------------------

def test_rotate_re_encrypts_value():
    env = {"API_KEY": _enc("hunter2")}
    result = rotate(env, OLD_PASS, NEW_PASS)
    new_cipher = result.rotated["API_KEY"]
    assert decrypt_value(new_cipher, NEW_PASS) == "hunter2"


def test_rotate_skips_plain_values():
    env = {"PLAIN": "not-encrypted"}
    result = rotate(env, OLD_PASS, NEW_PASS)
    assert "PLAIN" in result.skipped
    assert result.rotated["PLAIN"] == "not-encrypted"


def test_rotate_mixed_env():
    env = {
        "SECRET": _enc("s3cr3t"),
        "PUBLIC": "visible",
    }
    result = rotate(env, OLD_PASS, NEW_PASS)
    assert "PUBLIC" in result.skipped
    assert "SECRET" not in result.skipped
    assert decrypt_value(result.rotated["SECRET"], NEW_PASS) == "s3cr3t"


def test_rotate_wrong_old_passphrase_marks_failed():
    env = {"KEY": _enc("value")}
    result = rotate(env, "wrong-pass", NEW_PASS)
    assert "KEY" in result.failed
    assert result.has_failures


def test_rotate_specific_keys_only():
    env = {
        "A": _enc("alpha"),
        "B": _enc("beta"),
    }
    result = rotate(env, OLD_PASS, NEW_PASS, keys=["A"])
    assert decrypt_value(result.rotated["A"], NEW_PASS) == "alpha"
    # B should be unchanged (still encrypted under OLD_PASS)
    assert result.rotated["B"] == env["B"]
    assert "B" in result.skipped


def test_rotate_raises_for_missing_keys():
    env = {"A": _enc("alpha")}
    with pytest.raises(RotationError, match="not found"):
        rotate(env, OLD_PASS, NEW_PASS, keys=["MISSING"])


def test_rotate_raises_for_non_dict_env():
    with pytest.raises(RotationError):
        rotate("not-a-dict", OLD_PASS, NEW_PASS)  # type: ignore
