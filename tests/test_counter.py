"""Tests for envoy.counter."""

import pytest

from envoy.counter import CountError, CountResult, count


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "DEBUG": "true",
        "EMPTY_VAR": "",
        "TOKEN": "xyz",
    }


def test_count_returns_count_result(sample_env):
    result = count(sample_env)
    assert isinstance(result, CountResult)


def test_total_matches_number_of_keys(sample_env):
    result = count(sample_env)
    assert result.total == 7


def test_secret_keys_detected(sample_env):
    result = count(sample_env)
    # DB_PASSWORD, API_KEY, TOKEN are secrets
    assert result.secret_count >= 2


def test_empty_count_correct(sample_env):
    result = count(sample_env)
    assert result.empty_count == 1


def test_non_empty_count_correct(sample_env):
    result = count(sample_env)
    assert result.non_empty_count == 6


def test_empty_plus_non_empty_equals_total(sample_env):
    result = count(sample_env)
    assert result.empty_count + result.non_empty_count == result.total


def test_longest_key(sample_env):
    result = count(sample_env)
    assert result.longest_key == "DB_PASSWORD"


def test_shortest_key(sample_env):
    result = count(sample_env)
    assert result.shortest_key in {"DEBUG", "TOKEN"}


def test_average_value_length_is_float(sample_env):
    result = count(sample_env)
    assert isinstance(result.average_value_length, float)
    assert result.average_value_length >= 0.0


def test_prefix_counts_groups_by_prefix(sample_env):
    result = count(sample_env)
    assert result.prefix_counts.get("DB") == 3
    assert result.prefix_counts.get("API") == 1


def test_keys_without_separator_not_in_prefix_counts():
    env = {"DEBUG": "1", "TOKEN": "abc"}
    result = count(env)
    assert result.prefix_counts == {}


def test_empty_env_returns_zero_result():
    result = count({})
    assert result.total == 0
    assert result.secret_count == 0
    assert result.empty_count == 0
    assert result.non_empty_count == 0


def test_has_secrets_true_when_secrets_present(sample_env):
    result = count(sample_env)
    assert result.has_secrets() is True


def test_has_secrets_false_when_no_secrets():
    result = count({"DEBUG": "true", "LOG_LEVEL": "info"})
    assert result.has_secrets() is False


def test_has_empty_true_when_empty_value_present(sample_env):
    result = count(sample_env)
    assert result.has_empty() is True


def test_has_empty_false_when_all_values_set():
    result = count({"FOO": "bar", "BAZ": "qux"})
    assert result.has_empty() is False


def test_summary_contains_total(sample_env):
    result = count(sample_env)
    assert "7" in result.summary()


def test_summary_contains_prefix_breakdown(sample_env):
    result = count(sample_env)
    summary = result.summary()
    assert "DB_*" in summary
    assert "API_*" in summary


def test_non_dict_raises_count_error():
    with pytest.raises(CountError):
        count(["KEY=VALUE"])  # type: ignore
