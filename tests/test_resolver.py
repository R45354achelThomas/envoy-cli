"""Tests for envoy.resolver."""

from __future__ import annotations

import pytest

from envoy.resolver import resolve, ResolveError


@pytest.fixture()
def base_env(tmp_path):
    p = tmp_path / "base.env"
    p.write_text("APP=base\nDEBUG=false\nSECRET=abc123\n")
    return str(p)


@pytest.fixture()
def override_env(tmp_path):
    p = tmp_path / "override.env"
    p.write_text("APP=override\nEXTRA=hello\n")
    return str(p)


@pytest.fixture()
def second_override_env(tmp_path):
    p = tmp_path / "second.env"
    p.write_text("APP=second\nNEW_KEY=world\n")
    return str(p)


def test_single_file_resolves_all_keys(base_env):
    env = resolve([base_env])
    assert env.get("APP") == "base"
    assert env.get("DEBUG") == "false"
    assert env.get("SECRET") == "abc123"


def test_last_wins_by_default(base_env, override_env):
    env = resolve([base_env, override_env])
    assert env.get("APP") == "override"


def test_first_wins_mode(base_env, override_env):
    env = resolve([base_env, override_env], last_wins=False)
    assert env.get("APP") == "base"


def test_unique_key_from_second_file_present(base_env, override_env):
    env = resolve([base_env, override_env])
    assert env.get("EXTRA") == "hello"
    assert env.get("DEBUG") == "false"


def test_source_of_returns_winning_file(base_env, override_env):
    env = resolve([base_env, override_env])
    assert env.source_of("APP") == override_env
    assert env.source_of("DEBUG") == base_env


def test_was_overridden_true_for_duplicate_key(base_env, override_env):
    env = resolve([base_env, override_env])
    assert env.was_overridden("APP") is True


def test_was_overridden_false_for_unique_key(base_env, override_env):
    env = resolve([base_env, override_env])
    assert env.was_overridden("DEBUG") is False


def test_three_files_last_wins(base_env, override_env, second_override_env):
    env = resolve([base_env, override_env, second_override_env])
    assert env.get("APP") == "second"
    assert env.get("NEW_KEY") == "world"


def test_missing_file_raises_resolve_error(tmp_path):
    with pytest.raises(ResolveError, match="Failed to parse"):
        resolve([str(tmp_path / "nonexistent.env")])


def test_empty_file_list_raises_resolve_error():
    with pytest.raises(ResolveError, match="At least one"):
        resolve([])


def test_summary_mentions_overridden_keys(base_env, override_env):
    env = resolve([base_env, override_env])
    summary = env.summary()
    assert "APP" in summary
    assert "Overridden" in summary


def test_get_returns_default_for_missing_key(base_env):
    env = resolve([base_env])
    assert env.get("NONEXISTENT", "fallback") == "fallback"
