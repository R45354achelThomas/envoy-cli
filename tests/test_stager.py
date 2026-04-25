"""Tests for envoy.stager."""
import pytest
from envoy.stager import stage, StageResult


@pytest.fixture
def source_env():
    return {"DB_HOST": "prod-db", "DB_PORT": "5432", "SECRET_KEY": "abc123"}


@pytest.fixture
def target_env():
    return {"DB_HOST": "staging-db", "APP_ENV": "staging"}


def test_stage_returns_stage_result(source_env, target_env):
    result = stage(source_env, target_env)
    assert isinstance(result, StageResult)


def test_all_source_keys_staged_by_default(source_env, target_env):
    result = stage(source_env, target_env)
    for key in source_env:
        assert key in result.staged


def test_target_only_keys_preserved(source_env, target_env):
    result = stage(source_env, target_env)
    assert "APP_ENV" in result.staged
    assert result.staged["APP_ENV"] == "staging"


def test_source_values_overwrite_target_by_default(source_env, target_env):
    result = stage(source_env, target_env)
    assert result.staged["DB_HOST"] == "prod-db"


def test_overwrite_false_skips_existing_keys(source_env, target_env):
    result = stage(source_env, target_env, overwrite=False)
    assert result.staged["DB_HOST"] == "staging-db"  # not overwritten
    assert "DB_HOST" in result.skipped


def test_overwrite_false_stages_new_keys(source_env, target_env):
    result = stage(source_env, target_env, overwrite=False)
    assert result.staged["DB_PORT"] == "5432"
    assert result.staged["SECRET_KEY"] == "abc123"


def test_specific_keys_only_staged(source_env, target_env):
    result = stage(source_env, target_env, keys=["SECRET_KEY"])
    assert result.staged["SECRET_KEY"] == "abc123"
    assert result.staged.get("DB_PORT") is None


def test_missing_key_in_source_is_skipped(source_env, target_env):
    result = stage(source_env, target_env, keys=["NONEXISTENT"])
    assert "NONEXISTENT" in result.skipped
    assert not result.staged.get("NONEXISTENT")


def test_has_skipped_true_when_skipped(source_env, target_env):
    result = stage(source_env, target_env, keys=["NONEXISTENT"])
    assert result.has_skipped()


def test_has_skipped_false_when_none_skipped(source_env):
    result = stage(source_env, {}, source_env="dev", target_env="staging")
    assert not result.has_skipped()


def test_overwritten_keys_tracked(source_env, target_env):
    result = stage(source_env, target_env)
    assert "DB_HOST" in result.overwritten


def test_has_overwritten_true(source_env, target_env):
    result = stage(source_env, target_env)
    assert result.has_overwritten()


def test_has_overwritten_false_when_no_conflicts(source_env):
    result = stage(source_env, {}, source_env="dev", target_env="staging")
    assert not result.has_overwritten()


def test_summary_contains_env_names(source_env, target_env):
    result = stage(source_env, target_env, source_env="production", target_env="staging")
    assert "production" in result.summary()
    assert "staging" in result.summary()


def test_summary_mentions_overwritten(source_env, target_env):
    result = stage(source_env, target_env)
    assert "Overwrote" in result.summary()


def test_empty_source_produces_empty_staged_from_source():
    result = stage({}, {"KEEP": "me"}, source_env="dev", target_env="prod")
    assert result.staged == {"KEEP": "me"}
    assert not result.has_skipped()
