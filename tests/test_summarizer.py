"""Tests for envoy.summarizer."""
import pytest

from envoy.summarizer import SummarizeError, SummarizeResult, summarize


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "API_SECRET": "xyz789",
        "DEBUG": "true",
        "EMPTY_VAR": "",
        "ANOTHER_EMPTY": "",
        "APP_NAME": "myapp",
    }


def test_summarize_returns_summarize_result(sample_env):
    result = summarize(sample_env)
    assert isinstance(result, SummarizeResult)


def test_total_matches_number_of_keys(sample_env):
    result = summarize(sample_env)
    assert result.total == len(sample_env)


def test_secret_keys_detected(sample_env):
    result = summarize(sample_env)
    # DB_PASSWORD, API_KEY, API_SECRET are secrets
    assert result.secret_count >= 3


def test_empty_count_correct(sample_env):
    result = summarize(sample_env)
    assert result.empty_count == 2


def test_unique_values_correct(sample_env):
    result = summarize(sample_env)
    # Two empty strings count as one unique value
    assert result.unique_values == len(set(sample_env.values()))


def test_longest_key(sample_env):
    result = summarize(sample_env)
    expected = max(sample_env.keys(), key=len)
    assert result.longest_key == expected


def test_shortest_key(sample_env):
    result = summarize(sample_env)
    expected = min(sample_env.keys(), key=len)
    assert result.shortest_key == expected


def test_top_prefixes_groups_db_and_api(sample_env):
    result = summarize(sample_env)
    # DB appears 3 times, API appears 2 times
    assert "DB" in result.top_prefixes
    assert "API" in result.top_prefixes
    assert result.top_prefixes["DB"] == 3
    assert result.top_prefixes["API"] == 2


def test_single_occurrence_prefix_excluded(sample_env):
    result = summarize(sample_env)
    # APP appears only once, should not be in top_prefixes
    assert "APP" not in result.top_prefixes


def test_has_secrets_true(sample_env):
    result = summarize(sample_env)
    assert result.has_secrets() is True


def test_has_secrets_false():
    env = {"DEBUG": "true", "HOST": "localhost"}
    result = summarize(env)
    assert result.has_secrets() is False


def test_has_empty_true(sample_env):
    result = summarize(sample_env)
    assert result.has_empty() is True


def test_has_empty_false():
    env = {"HOST": "localhost", "PORT": "8080"}
    result = summarize(env)
    assert result.has_empty() is False


def test_summary_contains_total(sample_env):
    result = summarize(sample_env)
    assert "Total keys" in result.summary()
    assert str(result.total) in result.summary()


def test_empty_env_returns_zero_counts():
    result = summarize({})
    assert result.total == 0
    assert result.secret_count == 0
    assert result.empty_count == 0
    assert result.unique_values == 0
    assert result.longest_key == ""
    assert result.shortest_key == ""


def test_invalid_input_raises():
    with pytest.raises(SummarizeError):
        summarize(["not", "a", "dict"])  # type: ignore


def test_keys_list_matches_env_keys(sample_env):
    result = summarize(sample_env)
    assert set(result.keys) == set(sample_env.keys())
