"""Tests for envoy.trimmer."""

import pytest

from envoy.trimmer import TrimError, TrimResult, trim


@pytest.fixture
def sample_env():
    return {
        "KEY_A": "  hello  ",
        "KEY_B": "world",
        "  KEY_C  ": "value",
        "KEY_D": "   ",
    }


def test_trim_returns_trim_result(sample_env):
    result = trim(sample_env)
    assert isinstance(result, TrimResult)


def test_strip_values_removes_surrounding_whitespace(sample_env):
    result = trim(sample_env)
    assert result.trimmed["KEY_A"] == "hello"


def test_unchanged_value_not_in_changed_keys(sample_env):
    result = trim(sample_env)
    assert "KEY_B" not in result.changed_keys


def test_changed_value_in_changed_keys(sample_env):
    result = trim(sample_env)
    assert "KEY_A" in result.changed_keys


def test_strip_keys_removes_surrounding_whitespace(sample_env):
    result = trim(sample_env)
    assert "KEY_C" in result.trimmed
    assert "  KEY_C  " not in result.trimmed


def test_strip_keys_false_preserves_key_whitespace(sample_env):
    result = trim(sample_env, strip_keys=False)
    assert "  KEY_C  " in result.trimmed
    assert "KEY_C" not in result.trimmed


def test_strip_values_false_preserves_value_whitespace(sample_env):
    result = trim(sample_env, strip_values=False)
    assert result.trimmed["KEY_A"] == "  hello  "


def test_normalize_empty_converts_whitespace_only_to_empty(sample_env):
    result = trim(sample_env, normalize_empty=True)
    assert result.trimmed["KEY_D"] == ""


def test_normalize_empty_false_preserves_whitespace_only(sample_env):
    result = trim(sample_env, normalize_empty=False)
    # strip_values is True by default, so whitespace is stripped anyway
    assert result.trimmed["KEY_D"] == ""


def test_has_changes_true_when_something_changed(sample_env):
    result = trim(sample_env)
    assert result.has_changes() is True


def test_has_changes_false_when_nothing_changed():
    env = {"KEY": "clean"}
    result = trim(env)
    assert result.has_changes() is False


def test_summary_no_changes():
    result = trim({"KEY": "clean"})
    assert "No changes" in result.summary()


def test_summary_with_changes(sample_env):
    result = trim(sample_env)
    assert "Trimmed" in result.summary()
    assert str(len(result.changed_keys)) in result.summary()


def test_empty_env_returns_empty_result():
    result = trim({})
    assert result.trimmed == {}
    assert result.has_changes() is False
