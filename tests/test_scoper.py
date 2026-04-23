"""Tests for envoy.scoper."""

import pytest

from envoy.scoper import ScopeError, ScopeResult, scope


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_PASSWORD": "secret",
        "REDIS_HOST": "127.0.0.1",
        "REDIS_PORT": "6379",
        "APP_NAME": "envoy",
        "DEBUG": "true",
    }


def test_scope_returns_scope_result(sample_env):
    result = scope(sample_env, scope="DB")
    assert isinstance(result, ScopeResult)


def test_db_scope_keeps_only_db_keys(sample_env):
    result = scope(sample_env, scope="DB")
    assert set(result.scoped.keys()) == {"HOST", "PORT", "PASSWORD"}


def test_redis_scope_keeps_only_redis_keys(sample_env):
    result = scope(sample_env, scope="REDIS")
    assert set(result.scoped.keys()) == {"HOST", "PORT"}


def test_strip_prefix_true_removes_prefix(sample_env):
    result = scope(sample_env, scope="DB", strip_prefix=True)
    assert "HOST" in result.scoped
    assert "DB_HOST" not in result.scoped


def test_strip_prefix_false_preserves_full_key(sample_env):
    result = scope(sample_env, scope="DB", strip_prefix=False)
    assert "DB_HOST" in result.scoped
    assert "HOST" not in result.scoped


def test_values_preserved_after_scoping(sample_env):
    result = scope(sample_env, scope="DB")
    assert result.scoped["HOST"] == "localhost"
    assert result.scoped["PORT"] == "5432"


def test_dropped_contains_non_matching_keys(sample_env):
    result = scope(sample_env, scope="DB")
    assert "REDIS_HOST" in result.dropped
    assert "APP_NAME" in result.dropped
    assert "DEBUG" in result.dropped


def test_has_dropped_true_when_keys_excluded(sample_env):
    result = scope(sample_env, scope="DB")
    assert result.has_dropped() is True


def test_has_dropped_false_when_all_match():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    result = scope(env, scope="DB")
    assert result.has_dropped() is False


def test_none_scope_returns_full_env(sample_env):
    result = scope(sample_env, scope=None)
    assert result.scoped == sample_env
    assert result.dropped == []


def test_empty_scope_string_returns_full_env(sample_env):
    result = scope(sample_env, scope="")
    assert result.scoped == sample_env


def test_empty_env_returns_empty_result():
    result = scope({}, scope="DB")
    assert result.scoped == {}
    assert result.dropped == []


def test_case_insensitive_matching_by_default():
    env = {"db_host": "localhost", "db_port": "5432", "APP": "x"}
    result = scope(env, scope="db")
    assert "host" in result.scoped
    assert "port" in result.scoped


def test_summary_contains_scope_name(sample_env):
    result = scope(sample_env, scope="DB")
    assert "'DB'" in result.summary()


def test_summary_counts_kept_and_dropped(sample_env):
    result = scope(sample_env, scope="DB")
    summary = result.summary()
    assert "3 key(s) kept" in summary
    assert "4 key(s) dropped" in summary
