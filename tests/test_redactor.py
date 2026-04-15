"""Tests for envoy.redactor."""

import pytest

from envoy.redactor import RedactResult, RedactError, redact, DEFAULT_PLACEHOLDER


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "supersecret",
        "API_TOKEN": "tok_abc123",
        "DEBUG": "true",
        "PASSWORD": "hunter2",
    }


def test_non_secret_keys_unchanged(sample_env):
    result = redact(sample_env)
    assert result.redacted["APP_NAME"] == "myapp"
    assert result.redacted["DEBUG"] == "true"


def test_secret_keys_replaced_with_default_placeholder(sample_env):
    result = redact(sample_env)
    for key in result.redacted_keys:
        assert result.redacted[key] == DEFAULT_PLACEHOLDER


def test_known_secret_keys_detected(sample_env):
    result = redact(sample_env)
    assert "SECRET_KEY" in result.redacted_keys
    assert "PASSWORD" in result.redacted_keys
    assert "API_TOKEN" in result.redacted_keys


def test_custom_placeholder(sample_env):
    result = redact(sample_env, placeholder="***")
    for key in result.redacted_keys:
        assert result.redacted[key] == "***"


def test_extra_keys_treated_as_secrets(sample_env):
    result = redact(sample_env, extra_keys=["DATABASE_URL"])
    assert "DATABASE_URL" in result.redacted_keys
    assert result.redacted["DATABASE_URL"] == DEFAULT_PLACEHOLDER


def test_keys_only_limits_redaction(sample_env):
    result = redact(sample_env, keys_only=["SECRET_KEY"])
    assert result.redacted_keys == ["SECRET_KEY"]
    # API_TOKEN is a secret but not in keys_only
    assert result.redacted["API_TOKEN"] == sample_env["API_TOKEN"]


def test_has_changes_true_when_secrets_present(sample_env):
    result = redact(sample_env)
    assert result.has_changes() is True


def test_has_changes_false_when_no_secrets():
    result = redact({"APP_NAME": "myapp", "DEBUG": "true"})
    assert result.has_changes() is False


def test_summary_lists_redacted_keys(sample_env):
    result = redact(sample_env)
    summary = result.summary()
    assert "secret" in summary.lower() or "redacted" in summary.lower()
    for key in result.redacted_keys:
        assert key in summary


def test_summary_no_changes_message():
    result = redact({"APP_NAME": "myapp"})
    assert "nothing redacted" in result.summary().lower()


def test_original_is_unchanged(sample_env):
    result = redact(sample_env)
    assert result.original == sample_env


def test_invalid_env_raises_redact_error():
    with pytest.raises(RedactError):
        redact("not-a-dict")  # type: ignore
