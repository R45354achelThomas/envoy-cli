"""Tests for envoy.stripper."""

import pytest
from envoy.stripper import StripResult, StripError, strip


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "APP_SECRET": "s3cr3t",
        "APP_DEBUG": "true",
        "LOG_LEVEL": "info",
    }


def test_strip_returns_strip_result(sample_env):
    result = strip(sample_env)
    assert isinstance(result, StripResult)


def test_no_criteria_returns_unchanged(sample_env):
    result = strip(sample_env)
    assert result.env == sample_env
    assert result.stripped_keys == []


def test_strip_exact_key(sample_env):
    result = strip(sample_env, keys=["LOG_LEVEL"])
    assert "LOG_LEVEL" not in result.env
    assert "LOG_LEVEL" in result.stripped_keys


def test_strip_multiple_exact_keys(sample_env):
    result = strip(sample_env, keys=["DB_HOST", "DB_PORT"])
    assert "DB_HOST" not in result.env
    assert "DB_PORT" not in result.env
    assert len(result.stripped_keys) == 2


def test_strip_preserves_other_keys(sample_env):
    result = strip(sample_env, keys=["LOG_LEVEL"])
    assert "DB_HOST" in result.env
    assert "REDIS_URL" in result.env


def test_strip_by_prefix(sample_env):
    result = strip(sample_env, prefix="DB_")
    assert "DB_HOST" not in result.env
    assert "DB_PORT" not in result.env
    assert "REDIS_URL" in result.env


def test_strip_by_pattern(sample_env):
    result = strip(sample_env, patterns=[r"^APP_"])
    assert "APP_SECRET" not in result.env
    assert "APP_DEBUG" not in result.env
    assert "DB_HOST" in result.env


def test_strip_pattern_partial_match(sample_env):
    result = strip(sample_env, patterns=[r"SECRET"])
    assert "APP_SECRET" not in result.env
    assert "APP_DEBUG" in result.env


def test_has_changes_true_when_stripped(sample_env):
    result = strip(sample_env, keys=["LOG_LEVEL"])
    assert result.has_changes() is True


def test_has_changes_false_when_nothing_stripped(sample_env):
    result = strip(sample_env)
    assert result.has_changes() is False


def test_summary_lists_stripped_keys(sample_env):
    result = strip(sample_env, keys=["LOG_LEVEL", "REDIS_URL"])
    summary = result.summary()
    assert "LOG_LEVEL" in summary
    assert "REDIS_URL" in summary
    assert "2" in summary


def test_summary_no_changes(sample_env):
    result = strip(sample_env)
    assert result.summary() == "No keys stripped."


def test_combined_criteria(sample_env):
    result = strip(sample_env, keys=["LOG_LEVEL"], prefix="DB_")
    assert "LOG_LEVEL" not in result.env
    assert "DB_HOST" not in result.env
    assert "DB_PORT" not in result.env
    assert "REDIS_URL" in result.env
    assert len(result.stripped_keys) == 3


def test_nonexistent_key_ignored(sample_env):
    result = strip(sample_env, keys=["DOES_NOT_EXIST"])
    assert result.env == sample_env
    assert result.stripped_keys == []
