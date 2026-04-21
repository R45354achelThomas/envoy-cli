"""Tests for envoy.pinner."""

import pytest

from envoy.pinner import PinError, PinResult, pin


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "s3cr3t",
    }


def test_pin_returns_pin_result(sample_env):
    result = pin(sample_env)
    assert isinstance(result, PinResult)


def test_pin_no_existing_captures_all_keys(sample_env):
    result = pin(sample_env)
    assert result.pinned == sample_env


def test_pin_no_existing_has_no_drift(sample_env):
    result = pin(sample_env)
    assert result.has_drift() is False
    assert result.drifted == []
    assert result.missing == []


def test_pin_specific_keys_only(sample_env):
    result = pin(sample_env, keys=["APP_NAME", "DB_HOST"])
    assert set(result.pinned.keys()) == {"APP_NAME", "DB_HOST"}


def test_pin_unknown_key_raises(sample_env):
    with pytest.raises(PinError, match="NOPE"):
        pin(sample_env, keys=["NOPE"])


def test_no_drift_when_env_matches_pin(sample_env):
    result = pin(sample_env, existing_pin=dict(sample_env))
    assert result.has_drift() is False
    assert result.drifted == []


def test_drifted_key_detected(sample_env):
    existing = dict(sample_env)
    existing["DB_HOST"] = "prod-db.example.com"
    result = pin(sample_env, existing_pin=existing)
    assert "DB_HOST" in result.drifted


def test_missing_key_detected(sample_env):
    existing = dict(sample_env)
    existing["REMOVED_KEY"] = "old-value"
    result = pin(sample_env, existing_pin=existing)
    assert "REMOVED_KEY" in result.missing
    assert result.has_drift() is True


def test_new_keys_detected(sample_env):
    existing = {"APP_NAME": "myapp"}  # subset
    result = pin(sample_env, existing_pin=existing)
    for k in ("DB_HOST", "DB_PORT", "SECRET_KEY"):
        assert k in result.new_keys


def test_summary_no_drift(sample_env):
    result = pin(sample_env)
    assert "pinned" in result.summary()
    assert "drifted" not in result.summary()


def test_summary_with_drift(sample_env):
    existing = dict(sample_env)
    existing["DB_PORT"] = "9999"
    result = pin(sample_env, existing_pin=existing)
    assert "drifted" in result.summary()
