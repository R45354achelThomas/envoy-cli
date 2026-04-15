"""Tests for envoy.filter."""

import pytest
from envoy.filter import FilterError, FilterResult, filter_env


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "SECRET_KEY": "abc123",
        "EMPTY_VAR": "",
        "APP_NAME": "myapp",
    }


def test_filter_returns_filter_result(sample_env):
    result = filter_env(sample_env)
    assert isinstance(result, FilterResult)


def test_no_criteria_matches_all(sample_env):
    result = filter_env(sample_env)
    assert result.matched == sample_env
    assert result.excluded == {}


def test_prefix_filter_keeps_matching_keys(sample_env):
    result = filter_env(sample_env, prefix="DB_")
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}


def test_prefix_filter_case_insensitive(sample_env):
    result = filter_env(sample_env, prefix="db_")
    assert "DB_HOST" in result.matched
    assert "DB_PORT" in result.matched


def test_pattern_filter_regex(sample_env):
    result = filter_env(sample_env, pattern=r"^DB_")
    assert set(result.matched.keys()) == {"DB_HOST", "DB_PORT"}


def test_pattern_filter_partial_match(sample_env):
    result = filter_env(sample_env, pattern="url")
    assert "REDIS_URL" in result.matched


def test_invalid_pattern_raises_filter_error(sample_env):
    with pytest.raises(FilterError, match="Invalid regex"):
        filter_env(sample_env, pattern="[invalid")


def test_exclude_empty_removes_blank_values(sample_env):
    result = filter_env(sample_env, exclude_empty=True)
    assert "EMPTY_VAR" not in result.matched
    assert "EMPTY_VAR" in result.excluded


def test_invert_swaps_sets(sample_env):
    normal = filter_env(sample_env, prefix="DB_")
    inverted = filter_env(sample_env, prefix="DB_", invert=True)
    assert normal.matched == inverted.excluded
    assert normal.excluded == inverted.matched


def test_has_matches_true_when_keys_present(sample_env):
    result = filter_env(sample_env, prefix="DB_")
    assert result.has_matches() is True


def test_has_matches_false_when_no_keys():
    result = filter_env({"FOO": "bar"}, prefix="NONEXISTENT_")
    assert result.has_matches() is False


def test_summary_string(sample_env):
    result = filter_env(sample_env, prefix="DB_")
    summary = result.summary()
    assert "2" in summary
    assert "matched" in summary


def test_combined_prefix_and_exclude_empty():
    env = {"DB_HOST": "localhost", "DB_PASSWORD": "", "APP_NAME": "x"}
    result = filter_env(env, prefix="DB_", exclude_empty=True)
    assert "DB_HOST" in result.matched
    assert "DB_PASSWORD" not in result.matched
    assert "APP_NAME" not in result.matched
