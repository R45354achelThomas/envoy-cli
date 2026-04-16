"""Tests for envoy.deduplicator."""
import pytest
from envoy.deduplicator import deduplicate, DeduplicateError, DeduplicateResult


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "SERVICE_NAME": "myapp",   # duplicate of APP_NAME
        "DB_HOST": "localhost",
        "CACHE_HOST": "localhost", # duplicate of DB_HOST
        "PORT": "8080",
    }


def test_deduplicate_returns_result(sample_env):
    result = deduplicate(sample_env)
    assert isinstance(result, DeduplicateResult)


def test_duplicate_values_removed(sample_env):
    result = deduplicate(sample_env)
    assert "SERVICE_NAME" not in result.env
    assert "CACHE_HOST" not in result.env


def test_first_occurrence_kept_by_default(sample_env):
    result = deduplicate(sample_env)
    assert "APP_NAME" in result.env
    assert "DB_HOST" in result.env


def test_unique_keys_preserved(sample_env):
    result = deduplicate(sample_env)
    assert result.env["APP_NAME"] == "myapp"
    assert result.env["PORT"] == "8080"


def test_removed_keys_listed(sample_env):
    result = deduplicate(sample_env)
    assert "SERVICE_NAME" in result.removed_keys
    assert "CACHE_HOST" in result.removed_keys


def test_has_changes_true_when_duplicates(sample_env):
    result = deduplicate(sample_env)
    assert result.has_changes() is True


def test_has_changes_false_when_no_duplicates():
    env = {"A": "1", "B": "2", "C": "3"}
    result = deduplicate(env)
    assert result.has_changes() is False


def test_summary_mentions_removed_keys(sample_env):
    result = deduplicate(sample_env)
    assert "SERVICE_NAME" in result.summary() or "CACHE_HOST" in result.summary()


def test_summary_no_changes():
    result = deduplicate({"X": "unique"})
    assert "No duplicate" in result.summary()


def test_keep_last_retains_last_occurrence():
    env = {"A": "same", "B": "other", "C": "same"}
    result = deduplicate(env, keep="last")
    assert "C" in result.env
    assert "A" not in result.env


def test_invalid_keep_raises():
    with pytest.raises(DeduplicateError):
        deduplicate({"A": "1"}, keep="middle")


def test_ignore_keys_not_deduplicated():
    env = {"A": "val", "B": "val", "C": "val"}
    result = deduplicate(env, ignore_keys=["B"])
    # B is ignored so A is kept, C is removed as dup of A; B stays
    assert "B" in result.env
    assert "A" in result.env


def test_empty_env_returns_empty():
    result = deduplicate({})
    assert result.env == {}
    assert result.removed_keys == []
