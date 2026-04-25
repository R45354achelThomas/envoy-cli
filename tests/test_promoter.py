"""Tests for envoy.promoter."""
import pytest
from envoy.promoter import PromoteError, PromoteResult, promote


@pytest.fixture
def source_env():
    return {"DB_HOST": "prod-db", "DB_PORT": "5432", "SECRET_KEY": "abc123", "NEW_KEY": "new"}


@pytest.fixture
def target_env():
    return {"DB_HOST": "staging-db", "DB_PORT": "5432", "APP_ENV": "staging"}


def test_promote_returns_promote_result(source_env, target_env):
    result = promote(source_env, target_env)
    assert isinstance(result, PromoteResult)


def test_new_key_promoted_without_conflict(source_env, target_env):
    result = promote(source_env, target_env)
    assert "NEW_KEY" in result.promoted
    assert result.promoted["NEW_KEY"] == "new"


def test_identical_value_promoted_no_conflict(source_env, target_env):
    result = promote(source_env, target_env)
    assert "DB_PORT" in result.promoted
    assert "DB_PORT" not in result.conflicts


def test_differing_value_detected_as_conflict(source_env, target_env):
    result = promote(source_env, target_env)
    assert "DB_HOST" in result.conflicts
    assert result.conflicts["DB_HOST"] == ("prod-db", "staging-db")


def test_conflict_not_promoted_without_overwrite(source_env, target_env):
    result = promote(source_env, target_env, overwrite=False)
    assert "DB_HOST" not in result.promoted


def test_conflict_promoted_with_overwrite(source_env, target_env):
    result = promote(source_env, target_env, overwrite=True)
    assert "DB_HOST" in result.promoted
    assert result.promoted["DB_HOST"] == "prod-db"


def test_has_conflicts_true_when_conflicts_exist(source_env, target_env):
    result = promote(source_env, target_env)
    assert result.has_conflicts() is True


def test_has_conflicts_false_when_no_conflicts():
    src = {"ONLY_IN_SRC": "value"}
    tgt = {"ONLY_IN_TGT": "other"}
    result = promote(src, tgt)
    assert result.has_conflicts() is False


def test_has_changes_false_when_all_conflict_and_no_overwrite(source_env, target_env):
    src = {"DB_HOST": "prod-db"}
    tgt = {"DB_HOST": "staging-db"}
    result = promote(src, tgt, overwrite=False)
    assert result.has_changes() is False


def test_keys_filter_limits_promotion(source_env, target_env):
    result = promote(source_env, target_env, keys=["NEW_KEY"])
    assert "NEW_KEY" in result.promoted
    assert "SECRET_KEY" not in result.promoted
    assert "DB_HOST" not in result.promoted


def test_missing_key_in_source_goes_to_skipped(source_env, target_env):
    result = promote(source_env, target_env, keys=["DOES_NOT_EXIST"])
    assert "DOES_NOT_EXIST" in result.skipped


def test_summary_string_contains_counts(source_env, target_env):
    result = promote(source_env, target_env)
    summary = result.summary()
    assert "promoted=" in summary
    assert "conflicts=" in summary
    assert "skipped=" in summary


def test_source_path_and_target_path_stored():
    result = promote({}, {}, source_path="a.env", target_path="b.env")
    assert result.source_path == "a.env"
    assert result.target_path == "b.env"
