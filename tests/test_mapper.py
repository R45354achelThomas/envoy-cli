"""Tests for envoy.mapper."""
import pytest

from envoy.mapper import MapError, MapResult, map_env


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "SECRET_KEY": "abc123",
    }


def test_map_returns_map_result(sample_env):
    result = map_env(sample_env, {})
    assert isinstance(result, MapResult)


def test_no_mapping_returns_all_keys_unchanged(sample_env):
    result = map_env(sample_env, {})
    assert result.env == sample_env


def test_single_key_renamed(sample_env):
    result = map_env(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.env
    assert "DB_HOST" not in result.env
    assert result.env["DATABASE_HOST"] == "localhost"


def test_mapped_key_appears_in_mapped_keys(sample_env):
    result = map_env(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_HOST" in result.mapped_keys


def test_unmapped_key_appears_in_skipped_keys(sample_env):
    result = map_env(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_PORT" in result.skipped_keys


def test_none_mapping_drops_key(sample_env):
    result = map_env(sample_env, {"SECRET_KEY": None})
    assert "SECRET_KEY" not in result.env
    assert "SECRET_KEY" in result.dropped_keys


def test_drop_unmapped_excludes_other_keys(sample_env):
    result = map_env(sample_env, {"DB_HOST": "DATABASE_HOST"}, drop_unmapped=True)
    assert list(result.env.keys()) == ["DATABASE_HOST"]


def test_drop_unmapped_keys_appear_in_skipped(sample_env):
    result = map_env(sample_env, {"DB_HOST": "DATABASE_HOST"}, drop_unmapped=True)
    assert "DB_PORT" in result.skipped_keys
    assert "REDIS_URL" in result.skipped_keys


def test_has_changes_true_when_keys_mapped(sample_env):
    result = map_env(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.has_changes() is True


def test_has_changes_false_when_no_mapping(sample_env):
    result = map_env(sample_env, {})
    assert result.has_changes() is False


def test_has_changes_true_when_key_dropped(sample_env):
    result = map_env(sample_env, {"SECRET_KEY": None})
    assert result.has_changes() is True


def test_summary_reports_mapped_count(sample_env):
    result = map_env(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert "1 key(s) mapped" in result.summary()


def test_summary_reports_dropped_count(sample_env):
    result = map_env(sample_env, {"SECRET_KEY": None})
    assert "1 key(s) dropped" in result.summary()


def test_collision_raises_map_error(sample_env):
    # Map two different keys to the same target
    with pytest.raises(MapError, match="collision"):
        map_env(sample_env, {"DB_HOST": "CLASH", "DB_PORT": "CLASH"})


def test_invalid_mapping_type_raises_map_error(sample_env):
    with pytest.raises(MapError):
        map_env(sample_env, "not-a-dict")  # type: ignore


def test_values_preserved_after_rename(sample_env):
    result = map_env(sample_env, {"REDIS_URL": "CACHE_URL"})
    assert result.env["CACHE_URL"] == "redis://localhost"
