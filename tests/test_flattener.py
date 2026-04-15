"""Tests for envoy.flattener."""
import pytest

from envoy.flattener import FlattenError, FlattenResult, flatten


@pytest.fixture
def sample_env():
    return {
        "DB__HOST": "localhost",
        "DB__PORT": "5432",
        "REDIS__HOST": "127.0.0.1",
        "APP__NAME": "myapp",
        "PLAIN": "value",
    }


def test_flatten_returns_flatten_result(sample_env):
    result = flatten(sample_env)
    assert isinstance(result, FlattenResult)


def test_double_underscore_collapsed_to_single(sample_env):
    result = flatten(sample_env)
    assert "DB_HOST" in result.flattened
    assert "DB_PORT" in result.flattened


def test_plain_key_unchanged(sample_env):
    result = flatten(sample_env)
    assert result.flattened["PLAIN"] == "value"


def test_values_preserved(sample_env):
    result = flatten(sample_env)
    assert result.flattened["DB_HOST"] == "localhost"
    assert result.flattened["REDIS_HOST"] == "127.0.0.1"


def test_renamed_keys_listed(sample_env):
    result = flatten(sample_env)
    assert "DB__HOST" in result.renamed
    assert "PLAIN" not in result.renamed


def test_strip_prefix_removes_leading_segment():
    env = {"APP__DEBUG": "true", "APP__PORT": "8000", "OTHER": "x"}
    result = flatten(env, strip_prefix="APP")
    assert "DEBUG" in result.flattened
    assert "PORT" in result.flattened
    assert "OTHER" in result.flattened
    assert "APP__DEBUG" not in result.flattened


def test_strip_prefix_case_insensitive():
    env = {"app__key": "val"}
    result = flatten(env, strip_prefix="APP")
    assert "key" in result.flattened


def test_lowercase_option():
    env = {"DB__HOST": "localhost"}
    result = flatten(env, lowercase=True)
    assert "db_host" in result.flattened


def test_collision_skip_keeps_first():
    # Both collapse to DB_HOST
    env = {"DB__HOST": "first", "DB___HOST": "second"}
    result = flatten(env, separator="__")
    # One will collide — the second should be skipped
    assert len(result.skipped) >= 1


def test_collision_overwrite_keeps_last():
    env = {"A__B": "first", "A___B": "last"}
    # With overwrite, last writer wins
    result = flatten(env, separator="__", collision="overwrite")
    assert result.flattened.get("A_B") == "last"
    assert not result.skipped


def test_has_changes_false_when_no_renames_or_skips():
    env = {"KEY": "val"}
    result = flatten(env)
    assert not result.has_changes()


def test_has_changes_true_when_renamed(sample_env):
    result = flatten(sample_env)
    assert result.has_changes()


def test_summary_contains_key_count(sample_env):
    result = flatten(sample_env)
    assert "key(s)" in result.summary()


def test_invalid_collision_raises():
    with pytest.raises(FlattenError, match="collision"):
        flatten({"A": "1"}, collision="merge")


def test_empty_separator_raises():
    with pytest.raises(FlattenError, match="separator"):
        flatten({"A": "1"}, separator="")


def test_empty_env_returns_empty_result():
    result = flatten({})
    assert result.flattened == {}
    assert not result.renamed
    assert not result.skipped
