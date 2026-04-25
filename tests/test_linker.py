"""Tests for envoy.linker."""
import pytest

from envoy.linker import LinkError, LinkResult, link


@pytest.fixture
def envs():
    return {
        "dev": {"DB_HOST": "localhost", "DB_PORT": "5432", "DEBUG": "true"},
        "staging": {"DB_HOST": "staging-db", "DB_PORT": "5432", "REDIS_URL": "redis://staging"},
        "prod": {"DB_HOST": "prod-db", "DB_PORT": "5432", "SENTRY_DSN": "https://sentry.io/x"},
    }


def test_link_returns_link_result(envs):
    result = link(envs)
    assert isinstance(result, LinkResult)


def test_sources_preserved_in_order(envs):
    result = link(envs)
    assert result.sources == ["dev", "staging", "prod"]


def test_shared_keys_appear_in_all_three(envs):
    result = link(envs)
    assert "DB_HOST" in result.shared
    assert "DB_PORT" in result.shared


def test_shared_key_lists_all_sources(envs):
    result = link(envs)
    assert set(result.shared["DB_HOST"]) == {"dev", "staging", "prod"}


def test_unique_key_only_in_one_source(envs):
    result = link(envs)
    assert "DEBUG" in result.unique
    assert result.unique["DEBUG"] == "dev"


def test_unique_key_redis_url(envs):
    result = link(envs)
    assert "REDIS_URL" in result.unique
    assert result.unique["REDIS_URL"] == "staging"


def test_all_keys_includes_every_key(envs):
    result = link(envs)
    expected = {"DB_HOST", "DB_PORT", "DEBUG", "REDIS_URL", "SENTRY_DSN"}
    assert result.all_keys == expected


def test_has_shared_true_when_overlap(envs):
    result = link(envs)
    assert result.has_shared() is True


def test_has_unique_true_when_exclusive_keys(envs):
    result = link(envs)
    assert result.has_unique() is True


def test_has_shared_false_when_no_overlap():
    result = link({"a": {"FOO": "1"}, "b": {"BAR": "2"}})
    assert result.has_shared() is False


def test_has_unique_false_when_all_shared():
    result = link({"a": {"FOO": "1"}, "b": {"FOO": "2"}})
    assert result.has_unique() is False


def test_sources_for_shared_key(envs):
    result = link(envs)
    sources = result.sources_for("DB_HOST")
    assert set(sources) == {"dev", "staging", "prod"}


def test_sources_for_unique_key(envs):
    result = link(envs)
    assert result.sources_for("DEBUG") == ["dev"]


def test_sources_for_unknown_key(envs):
    result = link(envs)
    assert result.sources_for("NONEXISTENT") == []


def test_empty_envs_raises_link_error():
    with pytest.raises(LinkError):
        link({})


def test_summary_contains_counts(envs):
    result = link(envs)
    summary = result.summary()
    assert "3" in summary  # 3 sources
    assert str(len(result.all_keys)) in summary
