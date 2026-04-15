"""Tests for envoy.grouper."""
import pytest

from envoy.grouper import GroupError, GroupResult, group


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "REDIS_TTL": "300",
        "APP_NAME": "envoy",
        "PORT": "8080",
    }


def test_group_returns_group_result(sample_env):
    result = group(sample_env)
    assert isinstance(result, GroupResult)


def test_keys_grouped_by_prefix(sample_env):
    result = group(sample_env)
    assert "DB" in result.groups
    assert "REDIS" in result.groups
    assert "APP" in result.groups


def test_db_group_contains_correct_keys(sample_env):
    result = group(sample_env)
    assert set(result.groups["DB"].keys()) == {"DB_HOST", "DB_PORT"}


def test_redis_group_contains_correct_keys(sample_env):
    result = group(sample_env)
    assert set(result.groups["REDIS"].keys()) == {"REDIS_URL", "REDIS_TTL"}


def test_short_prefix_lands_in_ungrouped():
    env = {"X_THING": "val", "DB_HOST": "h"}
    result = group(env, min_prefix_length=2)
    assert "X_THING" in result.ungrouped
    assert "DB" in result.groups


def test_has_ungrouped_true_when_ungrouped_keys(sample_env):
    result = group(sample_env)
    # PORT has no underscore segment so it is ungrouped
    assert result.has_ungrouped()
    assert "PORT" in result.ungrouped


def test_has_ungrouped_false_when_all_grouped():
    env = {"DB_HOST": "h", "DB_PORT": "5432"}
    result = group(env)
    assert not result.has_ungrouped()


def test_group_names_sorted(sample_env):
    result = group(sample_env)
    assert result.group_names() == sorted(result.group_names())


def test_summary_contains_group_names(sample_env):
    result = group(sample_env)
    summary = result.summary()
    assert "DB" in summary
    assert "REDIS" in summary


def test_prefix_map_overrides_auto_grouping():
    env = {"DATABASE_URL": "pg://", "DB_HOST": "h", "REDIS_URL": "r://"}
    result = group(env, prefix_map={"DATABASE": "database", "DB": "database", "REDIS": "cache"})
    assert "database" in result.groups
    assert "cache" in result.groups
    assert set(result.groups["database"].keys()) == {"DATABASE_URL", "DB_HOST"}


def test_prefix_map_unmatched_goes_to_ungrouped():
    env = {"AWS_KEY": "k", "UNKNOWN": "u"}
    result = group(env, prefix_map={"AWS": "cloud"})
    assert "UNKNOWN" in result.ungrouped


def test_custom_separator():
    env = {"APP.NAME": "x", "APP.PORT": "80", "OTHER": "y"}
    result = group(env, separator=".")
    assert "APP" in result.groups


def test_invalid_env_raises():
    with pytest.raises(GroupError):
        group(["not", "a", "dict"])
