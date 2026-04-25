"""Tests for envoy.squasher."""
import pytest
from envoy.squasher import squash, SquashError, SquashResult


@pytest.fixture()
def base_env():
    return {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}


@pytest.fixture()
def override_env():
    return {"PORT": "9999", "SECRET_KEY": "abc123"}


def test_squash_returns_squash_result(base_env):
    result = squash([("base", base_env)])
    assert isinstance(result, SquashResult)


def test_single_env_unchanged(base_env):
    result = squash([("base", base_env)])
    assert result.env == base_env


def test_non_overlapping_keys_merged(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)])
    assert "HOST" in result.env
    assert "SECRET_KEY" in result.env


def test_last_wins_by_default(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)])
    assert result.env["PORT"] == "9999"


def test_first_wins_mode(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)], last_wins=False)
    assert result.env["PORT"] == "5432"


def test_sources_track_winning_file(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)])
    assert result.sources["PORT"] == "override"
    assert result.sources["HOST"] == "base"


def test_overridden_list_populated_on_conflict(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)])
    keys = [entry[0] for entry in result.overridden]
    assert "PORT" in keys


def test_overridden_contains_old_and_new_file(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)])
    entry = next(e for e in result.overridden if e[0] == "PORT")
    assert entry[1] == "base"
    assert entry[2] == "override"


def test_no_overrides_when_no_conflicts(base_env):
    extra = {"NEW_KEY": "val"}
    result = squash([("base", base_env), ("extra", extra)])
    assert not result.has_overrides()


def test_has_overrides_true_on_conflict(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)])
    assert result.has_overrides()


def test_summary_contains_key_count(base_env, override_env):
    result = squash([("base", base_env), ("override", override_env)])
    assert str(len(result.env)) in result.summary()


def test_empty_envs_raises():
    with pytest.raises(SquashError):
        squash([])


def test_three_files_last_wins():
    a = {"X": "1"}
    b = {"X": "2"}
    c = {"X": "3"}
    result = squash([("a", a), ("b", b), ("c", c)])
    assert result.env["X"] == "3"
    assert len(result.overridden) == 2
