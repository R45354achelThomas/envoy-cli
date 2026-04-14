"""Tests for envoy.duplicator."""

import pytest

from envoy.duplicator import DuplicateError, duplicate


@pytest.fixture
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DB_PASSWORD": "s3cr3t",
        "PORT": "8080",
        "DEBUG": "true",
    }


def test_duplicate_copies_all_keys_by_default(sample_env):
    result, output = duplicate(sample_env, "a.env", "b.env")
    assert set(output.keys()) == set(sample_env.keys())
    assert output["APP_NAME"] == "myapp"


def test_duplicate_values_preserved(sample_env):
    _, output = duplicate(sample_env, "a.env", "b.env")
    for k, v in sample_env.items():
        assert output[k] == v


def test_exclude_removes_key(sample_env):
    result, output = duplicate(sample_env, "a.env", "b.env", exclude=["DB_PASSWORD"])
    assert "DB_PASSWORD" not in output
    assert "DB_PASSWORD" in result.excluded_keys


def test_exclude_multiple_keys(sample_env):
    result, output = duplicate(sample_env, "a.env", "b.env", exclude=["DB_PASSWORD", "DEBUG"])
    assert "DB_PASSWORD" not in output
    assert "DEBUG" not in output
    assert len(result.excluded_keys) == 2


def test_rename_key(sample_env):
    result, output = duplicate(sample_env, "a.env", "b.env", rename={"PORT": "HTTP_PORT"})
    assert "HTTP_PORT" in output
    assert "PORT" not in output
    assert result.renamed_keys == {"PORT": "HTTP_PORT"}


def test_rename_preserves_value(sample_env):
    _, output = duplicate(sample_env, "a.env", "b.env", rename={"PORT": "HTTP_PORT"})
    assert output["HTTP_PORT"] == "8080"


def test_rename_and_exclude_combined(sample_env):
    result, output = duplicate(
        sample_env, "a.env", "b.env",
        exclude=["DEBUG"],
        rename={"APP_NAME": "SERVICE_NAME"},
    )
    assert "SERVICE_NAME" in output
    assert "APP_NAME" not in output
    assert "DEBUG" not in output
    assert result.excluded_keys == ["DEBUG"]
    assert result.renamed_keys == {"APP_NAME": "SERVICE_NAME"}


def test_included_keys_reflect_final_names(sample_env):
    result, _ = duplicate(sample_env, "a.env", "b.env", rename={"PORT": "HTTP_PORT"})
    assert "HTTP_PORT" in result.included_keys
    assert "PORT" not in result.included_keys


def test_has_changes_false_when_no_exclude_or_rename(sample_env):
    result, _ = duplicate(sample_env, "a.env", "b.env")
    assert result.has_changes() is False


def test_has_changes_true_when_excluded(sample_env):
    result, _ = duplicate(sample_env, "a.env", "b.env", exclude=["DEBUG"])
    assert result.has_changes() is True


def test_summary_contains_paths(sample_env):
    result, _ = duplicate(sample_env, "source.env", "dest.env")
    assert "source.env" in result.summary()
    assert "dest.env" in result.summary()


def test_summary_lists_excluded_keys(sample_env):
    result, _ = duplicate(sample_env, "a.env", "b.env", exclude=["DB_PASSWORD"])
    assert "DB_PASSWORD" in result.summary()


def test_rename_collision_raises(sample_env):
    # Rename PORT -> APP_NAME when APP_NAME already exists -> collision
    with pytest.raises(DuplicateError):
        duplicate(sample_env, "a.env", "b.env", rename={"PORT": "APP_NAME"})
