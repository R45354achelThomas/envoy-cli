"""Tests for envoy.sanitizer."""

import pytest

from envoy.sanitizer import sanitize, SanitizeResult, REDACT_PLACEHOLDER


@pytest.fixture()
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
    result = sanitize(sample_env)
    assert result.sanitized["APP_NAME"] == "myapp"
    assert result.sanitized["DEBUG"] == "true"


def test_secret_keys_redacted_by_default(sample_env):
    result = sanitize(sample_env)
    for key in ("SECRET_KEY", "API_TOKEN", "PASSWORD"):
        assert result.sanitized[key] == REDACT_PLACEHOLDER


def test_redacted_keys_listed_in_result(sample_env):
    result = sanitize(sample_env)
    assert "SECRET_KEY" in result.redacted_keys
    assert "PASSWORD" in result.redacted_keys


def test_remove_mode_excludes_secret_keys(sample_env):
    result = sanitize(sample_env, remove=True)
    assert "SECRET_KEY" not in result.sanitized
    assert "PASSWORD" not in result.sanitized
    assert "APP_NAME" in result.sanitized


def test_remove_mode_populates_removed_keys(sample_env):
    result = sanitize(sample_env, remove=True)
    assert "SECRET_KEY" in result.removed_keys
    assert len(result.redacted_keys) == 0


def test_custom_placeholder(sample_env):
    result = sanitize(sample_env, placeholder="***")
    assert result.sanitized["SECRET_KEY"] == "***"


def test_extra_keys_treated_as_secrets(sample_env):
    result = sanitize(sample_env, extra_keys=["DATABASE_URL"])
    assert result.sanitized["DATABASE_URL"] == REDACT_PLACEHOLDER
    assert "DATABASE_URL" in result.redacted_keys


def test_extra_keys_case_insensitive(sample_env):
    result = sanitize(sample_env, extra_keys=["database_url"])
    assert result.sanitized["DATABASE_URL"] == REDACT_PLACEHOLDER


def test_has_changes_true_when_secrets_present(sample_env):
    result = sanitize(sample_env)
    assert result.has_changes is True


def test_has_changes_false_when_no_secrets():
    result = sanitize({"APP": "hello", "ENV": "prod"})
    assert result.has_changes is False


def test_summary_mentions_redacted_count(sample_env):
    result = sanitize(sample_env)
    assert "Redacted" in result.summary()


def test_summary_no_changes_message():
    result = sanitize({"APP": "hello"})
    assert result.summary() == "No changes made."


def test_original_env_not_mutated(sample_env):
    original_copy = dict(sample_env)
    sanitize(sample_env)
    assert sample_env == original_copy
