"""Tests for envoy.differ."""
import pytest
from envoy.differ import differ, DifferError, DifferResult, DiffRecord


@pytest.fixture()
def old_env():
    return {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}


@pytest.fixture()
def new_env():
    return {"HOST": "prod.example.com", "PORT": "5432", "SECRET_KEY": "abc123"}


def test_differ_returns_differ_result(old_env, new_env):
    result = differ(old_env, new_env)
    assert isinstance(result, DifferResult)


def test_added_keys_detected(old_env, new_env):
    result = differ(old_env, new_env)
    keys = [r.key for r in result.added]
    assert "SECRET_KEY" in keys


def test_removed_keys_detected(old_env, new_env):
    result = differ(old_env, new_env)
    keys = [r.key for r in result.removed]
    assert "DEBUG" in keys


def test_changed_keys_detected(old_env, new_env):
    result = differ(old_env, new_env)
    keys = [r.key for r in result.changed]
    assert "HOST" in keys


def test_unchanged_excluded_by_default(old_env, new_env):
    result = differ(old_env, new_env)
    assert result.unchanged == []


def test_unchanged_included_when_requested(old_env, new_env):
    result = differ(old_env, new_env, include_unchanged=True)
    keys = [r.key for r in result.unchanged]
    assert "PORT" in keys


def test_has_differences_true_when_diffs_exist(old_env, new_env):
    result = differ(old_env, new_env)
    assert result.has_differences is True


def test_has_differences_false_for_identical_envs():
    env = {"A": "1", "B": "2"}
    result = differ(env, env.copy())
    assert result.has_differences is False


def test_summary_reports_counts(old_env, new_env):
    result = differ(old_env, new_env)
    summary = result.summary()
    assert "added" in summary
    assert "removed" in summary
    assert "changed" in summary


def test_summary_no_differences_message():
    env = {"X": "1"}
    result = differ(env, env.copy())
    assert result.summary() == "No differences found."


def test_diff_record_str_added():
    r = DiffRecord("FOO", "added", new_value="bar")
    assert str(r).startswith("+")


def test_diff_record_str_removed():
    r = DiffRecord("FOO", "removed", old_value="bar")
    assert str(r).startswith("-")


def test_diff_record_str_changed():
    r = DiffRecord("FOO", "changed", old_value="a", new_value="b")
    assert str(r).startswith("~")


def test_diff_record_str_unchanged():
    r = DiffRecord("FOO", "unchanged", old_value="a", new_value="a")
    assert str(r).startswith(" ")


def test_invalid_input_raises_differ_error():
    with pytest.raises(DifferError):
        differ("not a dict", {})  # type: ignore


def test_empty_envs_produce_no_records():
    result = differ({}, {})
    assert result.records == []
    assert result.has_differences is False
