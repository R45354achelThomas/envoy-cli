"""Tests for envoy.tagger."""

import pytest

from envoy.tagger import TagError, TagResult, tag


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "secret",
        "REDIS_URL": "redis://localhost",
        "APP_DEBUG": "true",
        "API_KEY": "abc123",
    }


def test_tag_returns_tag_result(sample_env):
    result = tag(sample_env, {"DB_HOST": ["database"]})
    assert isinstance(result, TagResult)


def test_tag_assigns_single_label(sample_env):
    result = tag(sample_env, {"DB_HOST": ["database"]})
    assert result.has_tag("DB_HOST", "database")


def test_tag_assigns_multiple_labels(sample_env):
    result = tag(sample_env, {"DB_PASSWORD": ["database", "secret"]})
    assert result.has_tag("DB_PASSWORD", "database")
    assert result.has_tag("DB_PASSWORD", "secret")


def test_tag_index_maps_tag_to_keys(sample_env):
    result = tag(
        sample_env,
        {
            "DB_HOST": ["database"],
            "DB_PASSWORD": ["database", "secret"],
        },
    )
    db_keys = result.keys_for_tag("database")
    assert "DB_HOST" in db_keys
    assert "DB_PASSWORD" in db_keys


def test_tags_for_key_returns_empty_set_for_untagged(sample_env):
    result = tag(sample_env, {"DB_HOST": ["database"]})
    assert result.tags_for_key("APP_DEBUG") == set()


def test_all_tags_returns_union(sample_env):
    result = tag(
        sample_env,
        {
            "DB_HOST": ["database"],
            "API_KEY": ["secret", "api"],
        },
    )
    assert result.all_tags() == {"database", "secret", "api"}


def test_missing_key_ignored_by_default(sample_env):
    result = tag(sample_env, {"NONEXISTENT": ["orphan"]})
    assert "NONEXISTENT" not in result.tags


def test_missing_key_raises_when_strict(sample_env):
    with pytest.raises(TagError, match="NONEXISTENT"):
        tag(sample_env, {"NONEXISTENT": ["orphan"]}, ignore_missing=False)


def test_env_preserved_in_result(sample_env):
    result = tag(sample_env, {"DB_HOST": ["database"]})
    assert result.env == sample_env


def test_summary_string(sample_env):
    result = tag(
        sample_env,
        {
            "DB_HOST": ["database"],
            "DB_PASSWORD": ["database", "secret"],
        },
    )
    summary = result.summary()
    assert "2 key(s)" in summary
    assert "2 unique tag(s)" in summary


def test_keys_for_missing_tag_returns_empty(sample_env):
    result = tag(sample_env, {"DB_HOST": ["database"]})
    assert result.keys_for_tag("nonexistent") == []
