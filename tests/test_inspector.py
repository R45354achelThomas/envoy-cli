"""Tests for envoy.inspector."""
import pytest

from envoy.inspector import inspect, InspectError, InspectResult


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "s3cret",
        "API_KEY": "abc123",
        "APP_NAME": "myapp",
        "EMPTY_VAR": "",
        "SECRET_TOKEN": "tok",
    }


def test_inspect_returns_inspect_result(sample_env):
    result = inspect(sample_env)
    assert isinstance(result, InspectResult)


def test_total_matches_number_of_keys(sample_env):
    result = inspect(sample_env)
    assert result.total == len(sample_env)


def test_secret_keys_detected(sample_env):
    result = inspect(sample_env)
    assert "DB_PASSWORD" in result.secret_keys
    assert "API_KEY" in result.secret_keys
    assert "SECRET_TOKEN" in result.secret_keys


def test_non_secret_keys_not_in_secrets(sample_env):
    result = inspect(sample_env)
    assert "DB_HOST" not in result.secret_keys
    assert "APP_NAME" not in result.secret_keys


def test_empty_keys_detected(sample_env):
    result = inspect(sample_env)
    assert "EMPTY_VAR" in result.empty_keys


def test_non_empty_keys_not_in_empty(sample_env):
    result = inspect(sample_env)
    assert "DB_HOST" not in result.empty_keys


def test_longest_key(sample_env):
    result = inspect(sample_env)
    assert result.longest_key == "SECRET_TOKEN"


def test_shortest_key(sample_env):
    result = inspect(sample_env)
    assert result.shortest_key == "DB_HOST"


def test_has_secrets_true(sample_env):
    result = inspect(sample_env)
    assert result.has_secrets is True


def test_has_secrets_false():
    result = inspect({"APP_NAME": "myapp", "PORT": "8080"})
    assert result.has_secrets is False


def test_has_empty_true(sample_env):
    result = inspect(sample_env)
    assert result.has_empty is True


def test_has_empty_false():
    result = inspect({"APP_NAME": "myapp", "PORT": "8080"})
    assert result.has_empty is False


def test_summary_contains_total(sample_env):
    result = inspect(sample_env)
    assert "Total keys" in result.summary()
    assert str(result.total) in result.summary()


def test_summary_contains_secret_count(sample_env):
    result = inspect(sample_env)
    assert "Secret keys" in result.summary()


def test_empty_env_returns_zero_total():
    result = inspect({})
    assert result.total == 0
    assert result.secret_keys == []
    assert result.empty_keys == []
    assert result.longest_key == ""
    assert result.shortest_key == ""


def test_non_dict_raises_inspect_error():
    with pytest.raises(InspectError):
        inspect(["KEY=VALUE"])  # type: ignore
