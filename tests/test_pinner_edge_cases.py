"""Edge-case tests for envoy.pinner."""

from envoy.pinner import PinError, pin
import pytest


def test_empty_env_no_drift():
    result = pin({}, existing_pin={})
    assert result.has_drift() is False
    assert result.pinned == {}


def test_empty_env_creates_empty_pin():
    result = pin({})
    assert result.pinned == {}


def test_multiple_drifted_keys():
    env = {"A": "1", "B": "2", "C": "3"}
    existing = {"A": "X", "B": "Y", "C": "3"}
    result = pin(env, existing_pin=existing)
    assert sorted(result.drifted) == ["A", "B"]
    assert result.drifted  # has_drift via drifted list


def test_summary_includes_new_count():
    env = {"A": "1", "B": "2"}
    existing = {"A": "1"}
    result = pin(env, existing_pin=existing)
    assert "new" in result.summary()


def test_pin_keys_subset_ignores_other_keys():
    env = {"A": "1", "B": "2", "C": "3"}
    result = pin(env, keys=["A", "B"])
    assert "C" not in result.pinned
    assert result.pinned == {"A": "1", "B": "2"}


def test_pin_keys_drift_only_within_subset():
    env = {"A": "new", "B": "2"}
    existing = {"A": "old", "B": "2"}
    result = pin(env, existing_pin=existing, keys=["B"])
    # Only B is in scope — no drift expected
    assert result.has_drift() is False


def test_multiple_missing_keys_all_reported():
    env = {"A": "1"}
    existing = {"A": "1", "B": "2", "C": "3"}
    result = pin(env, existing_pin=existing)
    assert set(result.missing) == {"B", "C"}


def test_pin_error_message_contains_bad_key():
    with pytest.raises(PinError) as exc_info:
        pin({"A": "1"}, keys=["A", "MISSING"])
    assert "MISSING" in str(exc_info.value)
