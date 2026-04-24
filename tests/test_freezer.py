"""Tests for envoy.freezer."""
import json
import pytest

from envoy.freezer import FreezeError, FreezeResult, freeze, _compute_digest


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "s3cr3t",
    }


# --- freeze() returns correct type ---

def test_freeze_returns_freeze_result(sample_env):
    result = freeze(sample_env)
    assert isinstance(result, FreezeResult)


def test_freeze_captures_all_keys(sample_env):
    result = freeze(sample_env)
    assert result.key_count == len(sample_env)
    assert result.env == sample_env


def test_freeze_subset_of_keys(sample_env):
    result = freeze(sample_env, keys=["APP_NAME", "DB_HOST"])
    assert set(result.env.keys()) == {"APP_NAME", "DB_HOST"}
    assert result.key_count == 2


def test_freeze_unknown_keys_silently_skipped(sample_env):
    result = freeze(sample_env, keys=["APP_NAME", "DOES_NOT_EXIST"])
    assert "DOES_NOT_EXIST" not in result.env
    assert result.key_count == 1


# --- digest correctness ---

def test_digest_is_hex_string(sample_env):
    result = freeze(sample_env)
    assert isinstance(result.digest, str)
    assert len(result.digest) == 64  # SHA-256 hex
    int(result.digest, 16)  # must be valid hex


def test_digest_is_deterministic(sample_env):
    r1 = freeze(sample_env)
    r2 = freeze(sample_env)
    assert r1.digest == r2.digest


def test_digest_changes_when_value_changes(sample_env):
    r1 = freeze(sample_env)
    modified = {**sample_env, "DB_PORT": "9999"}
    r2 = freeze(modified)
    assert r1.digest != r2.digest


def test_digest_changes_when_key_added(sample_env):
    r1 = freeze(sample_env)
    extended = {**sample_env, "NEW_KEY": "new_value"}
    r2 = freeze(extended)
    assert r1.digest != r2.digest


# --- has_drift ---

def test_has_drift_false_for_identical_envs(sample_env):
    r1 = freeze(sample_env)
    r2 = freeze(sample_env)
    assert not r1.has_drift(r2)


def test_has_drift_true_for_different_envs(sample_env):
    r1 = freeze(sample_env)
    r2 = freeze({**sample_env, "APP_NAME": "changed"})
    assert r1.has_drift(r2)


# --- summary ---

def test_summary_contains_key_count(sample_env):
    result = freeze(sample_env)
    assert str(len(sample_env)) in result.summary()


def test_summary_contains_digest_prefix(sample_env):
    result = freeze(sample_env)
    assert result.digest[:12] in result.summary()


# --- round-trip via to_dict / from_dict ---

def test_round_trip(sample_env):
    original = freeze(sample_env)
    restored = FreezeResult.from_dict(original.to_dict())
    assert restored.env == original.env
    assert restored.digest == original.digest


def test_from_dict_raises_on_tampered_digest(sample_env):
    data = freeze(sample_env).to_dict()
    data["digest"] = "deadbeef" * 8
    with pytest.raises(FreezeError, match="Digest mismatch"):
        FreezeResult.from_dict(data)


def test_from_dict_raises_on_missing_env():
    with pytest.raises(FreezeError, match="'env' must be a mapping"):
        FreezeResult.from_dict({"digest": "abc"})
