"""Tests for envoy.splitter."""
import pytest

from envoy.splitter import SplitError, SplitResult, split


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "REDIS_URL": "redis://localhost",
        "REDIS_TTL": "300",
        "APP_NAME": "envoy",
        "SECRET_KEY": "abc123",
        "DEBUG": "true",
    }


def test_split_returns_split_result(sample_env):
    result = split(sample_env)
    assert isinstance(result, SplitResult)


def test_keys_grouped_by_prefix(sample_env):
    result = split(sample_env)
    assert "DB" in result.buckets
    assert "REDIS" in result.buckets
    assert "APP" in result.buckets
    assert "SECRET" in result.buckets


def test_db_bucket_contains_correct_keys(sample_env):
    result = split(sample_env)
    assert "DB_HOST" in result.buckets["DB"]
    assert "DB_PORT" in result.buckets["DB"]


def test_ungrouped_key_has_no_separator(sample_env):
    result = split(sample_env)
    # DEBUG has no separator, so it lands in ungrouped
    assert "DEBUG" in result.ungrouped


def test_has_ungrouped_true_when_plain_keys_present(sample_env):
    result = split(sample_env)
    assert result.has_ungrouped is True


def test_has_ungrouped_false_when_all_prefixed():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    result = split(env)
    assert result.has_ungrouped is False


def test_explicit_prefixes_limit_buckets(sample_env):
    result = split(sample_env, prefixes=["DB"])
    assert list(result.buckets.keys()) == ["DB"]
    assert "REDIS_URL" in result.ungrouped


def test_keep_prefix_false_strips_prefix():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    result = split(env, keep_prefix=False)
    assert "HOST" in result.buckets["DB"]
    assert "PORT" in result.buckets["DB"]
    assert "DB_HOST" not in result.buckets["DB"]


def test_keep_prefix_true_preserves_key():
    env = {"DB_HOST": "localhost"}
    result = split(env, keep_prefix=True)
    assert "DB_HOST" in result.buckets["DB"]


def test_values_preserved(sample_env):
    result = split(sample_env)
    assert result.buckets["DB"]["DB_HOST"] == "localhost"
    assert result.buckets["REDIS"]["REDIS_URL"] == "redis://localhost"


def test_bucket_names_sorted(sample_env):
    result = split(sample_env)
    assert result.bucket_names == sorted(result.bucket_names)


def test_summary_includes_bucket_counts(sample_env):
    result = split(sample_env, prefixes=["DB", "REDIS"])
    s = result.summary()
    assert "DB" in s
    assert "REDIS" in s
    assert "2" in s  # DB has 2 keys


def test_summary_mentions_ungrouped(sample_env):
    result = split(sample_env)
    assert "ungrouped" in result.summary()


def test_empty_env_returns_empty_result():
    result = split({})
    assert result.buckets == {}
    assert result.ungrouped == {}
    assert result.summary() == "no keys"


def test_non_dict_raises_split_error():
    with pytest.raises(SplitError):
        split(["DB_HOST=localhost"])  # type: ignore[arg-type]


def test_custom_separator():
    env = {"DB.HOST": "localhost", "DB.PORT": "5432", "DEBUG": "true"}
    result = split(env, separator=".")
    assert "DB" in result.buckets
    assert "DEBUG" in result.ungrouped
