"""Tests for envoy.validator."""

import pytest
from envoy.validator import validate, ValidationResult, ValidationError


TEMPLATE = {
    "DATABASE_URL": None,       # required
    "SECRET_KEY": None,         # required
    "DEBUG": "false",           # optional with default
    "LOG_LEVEL": "INFO",        # optional with default
}


def test_valid_env_passes():
    env = {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc123"}
    result = validate(env, TEMPLATE)
    assert result.is_valid
    assert len(result.errors) == 0


def test_missing_required_key_is_error():
    env = {"DATABASE_URL": "postgres://localhost/db"}  # SECRET_KEY missing
    result = validate(env, TEMPLATE)
    assert not result.is_valid
    keys = [e.key for e in result.errors]
    assert "SECRET_KEY" in keys


def test_missing_optional_key_is_warning():
    env = {"DATABASE_URL": "postgres://localhost/db", "SECRET_KEY": "abc"}
    result = validate(env, TEMPLATE)
    assert result.is_valid
    warn_keys = [w.key for w in result.warnings]
    assert "DEBUG" in warn_keys
    assert "LOG_LEVEL" in warn_keys


def test_empty_required_value_is_warning():
    env = {"DATABASE_URL": "", "SECRET_KEY": "abc"}
    result = validate(env, TEMPLATE)
    assert result.is_valid  # empty required is a warning, not error
    warn_keys = [w.key for w in result.warnings]
    assert "DATABASE_URL" in warn_keys


def test_extra_keys_allowed_by_default():
    env = {"DATABASE_URL": "x", "SECRET_KEY": "y", "EXTRA_VAR": "z"}
    result = validate(env, TEMPLATE)
    assert result.is_valid
    warn_keys = [w.key for w in result.warnings]
    assert "EXTRA_VAR" not in warn_keys


def test_extra_keys_warned_when_not_allowed():
    env = {"DATABASE_URL": "x", "SECRET_KEY": "y", "EXTRA_VAR": "z"}
    result = validate(env, TEMPLATE, allow_extras=False)
    assert result.is_valid
    warn_keys = [w.key for w in result.warnings]
    assert "EXTRA_VAR" in warn_keys


def test_summary_all_passed():
    env = {"DATABASE_URL": "x", "SECRET_KEY": "y", "DEBUG": "true", "LOG_LEVEL": "DEBUG"}
    result = validate(env, TEMPLATE)
    assert "All checks passed" in result.summary()


def test_summary_contains_error_label():
    result = validate({}, TEMPLATE)
    summary = result.summary()
    assert "ERROR" in summary
    assert "DATABASE_URL" in summary
    assert "SECRET_KEY" in summary


def test_validation_error_str():
    err = ValidationError("MY_KEY", "something went wrong")
    assert str(err) == "[MY_KEY] something went wrong"
