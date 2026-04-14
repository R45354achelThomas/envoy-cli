"""Tests for envoy.renamer."""
import pytest

from envoy.renamer import RenameError, RenameResult, rename


@pytest.fixture
def sample_env():
    return {"DB_HOST": "localhost", "DB_PORT": "5432", "APP_SECRET": "s3cr3t"}


def test_rename_single_key(sample_env):
    result = rename(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DATABASE_HOST" in result.env
    assert "DB_HOST" not in result.env
    assert result.env["DATABASE_HOST"] == "localhost"


def test_rename_preserves_other_keys(sample_env):
    result = rename(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert "DB_PORT" in result.env
    assert "APP_SECRET" in result.env


def test_rename_multiple_keys(sample_env):
    result = rename(sample_env, {"DB_HOST": "DATABASE_HOST", "DB_PORT": "DATABASE_PORT"})
    assert len(result.renamed) == 2
    assert "DATABASE_HOST" in result.env
    assert "DATABASE_PORT" in result.env


def test_missing_old_key_is_skipped(sample_env):
    result = rename(sample_env, {"MISSING_KEY": "NEW_KEY"})
    assert len(result.renamed) == 0
    assert len(result.skipped) == 1
    assert result.skipped[0][0] == "MISSING_KEY"


def test_identical_names_skipped(sample_env):
    result = rename(sample_env, {"DB_HOST": "DB_HOST"})
    assert len(result.renamed) == 0
    assert result.skipped[0][1] == "old and new names are identical"


def test_no_overwrite_by_default(sample_env):
    result = rename(sample_env, {"DB_HOST": "DB_PORT"})
    assert len(result.skipped) == 1
    assert "already exists" in result.skipped[0][1]
    assert result.env["DB_PORT"] == "5432"  # original value preserved


def test_allow_overwrite_flag(sample_env):
    result = rename(sample_env, {"DB_HOST": "DB_PORT"}, allow_overwrite=True)
    assert len(result.renamed) == 1
    assert result.env["DB_PORT"] == "localhost"


def test_has_changes_true_when_renamed(sample_env):
    result = rename(sample_env, {"DB_HOST": "DATABASE_HOST"})
    assert result.has_changes is True


def test_has_changes_false_when_nothing_renamed(sample_env):
    result = rename(sample_env, {"MISSING": "OTHER"})
    assert result.has_changes is False


def test_summary_includes_counts(sample_env):
    result = rename(sample_env, {"DB_HOST": "DATABASE_HOST", "MISSING": "X"})
    summary = result.summary()
    assert "1 key(s) renamed" in summary
    assert "1 skipped" in summary


def test_non_dict_renames_raises():
    with pytest.raises(RenameError):
        rename({"A": "1"}, [("A", "B")])  # type: ignore[arg-type]


def test_non_string_key_raises():
    with pytest.raises(RenameError):
        rename({"A": "1"}, {1: "B"})  # type: ignore[arg-type]


def test_empty_renames_returns_unchanged(sample_env):
    result = rename(sample_env, {})
    assert result.env == sample_env
    assert result.has_changes is False
