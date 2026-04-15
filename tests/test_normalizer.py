"""Tests for envoy.normalizer."""
import pytest

from envoy.normalizer import NormalizeError, NormalizeResult, normalize


@pytest.fixture
def sample_env():
    return {
        "db_host": "localhost",
        "DB_PORT": "5432",
        "Api Key": "abc123",
        "SECRET": "  s3cr3t  ",
    }


def test_normalize_returns_normalize_result(sample_env):
    result = normalize(sample_env)
    assert isinstance(result, NormalizeResult)


def test_lowercase_key_uppercased(sample_env):
    result = normalize(sample_env)
    assert "DB_HOST" in result.normalized
    assert "db_host" not in result.normalized


def test_already_uppercase_key_unchanged(sample_env):
    result = normalize(sample_env)
    assert "DB_PORT" in result.normalized


def test_spaces_in_key_replaced_with_underscore(sample_env):
    result = normalize(sample_env)
    assert "API_KEY" in result.normalized
    assert "Api Key" not in result.normalized


def test_value_whitespace_stripped(sample_env):
    result = normalize(sample_env)
    assert result.normalized["SECRET"] == "s3cr3t"


def test_has_changes_true_when_keys_modified(sample_env):
    result = normalize(sample_env)
    assert result.has_changes() is True


def test_has_changes_false_when_already_normalized():
    env = {"DB_HOST": "localhost", "API_KEY": "abc"}
    result = normalize(env)
    assert result.has_changes() is False


def test_changed_keys_lists_original_names(sample_env):
    result = normalize(sample_env)
    assert "db_host" in result.changed_keys
    assert "Api Key" in result.changed_keys


def test_summary_no_changes():
    env = {"HOST": "localhost"}
    result = normalize(env)
    assert "already normalized" in result.summary()


def test_summary_with_changes(sample_env):
    result = normalize(sample_env)
    summary = result.summary()
    assert "normalized" in summary
    assert str(len(result.changed_keys)) in summary


def test_uppercase_keys_disabled():
    env = {"db_host": "localhost"}
    result = normalize(env, uppercase_keys=False)
    assert "db_host" in result.normalized


def test_strip_values_disabled():
    env = {"KEY": "  value  "}
    result = normalize(env, strip_values=False)
    assert result.normalized["KEY"] == "  value  "


def test_replace_spaces_disabled():
    env = {"my key": "val"}
    result = normalize(env, replace_spaces_in_keys=False, uppercase_keys=False)
    assert "my key" in result.normalized


def test_non_dict_raises_normalize_error():
    with pytest.raises(NormalizeError):
        normalize(["KEY=value"])  # type: ignore[arg-type]
