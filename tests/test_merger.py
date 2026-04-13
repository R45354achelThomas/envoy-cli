"""Tests for envoy.merger module."""

import pytest
from envoy.merger import merge_envs, MergeConflict, MergeResult


ENV_BASE = {"APP_NAME": "myapp", "DEBUG": "false", "PORT": "8080"}
ENV_PROD = {"DEBUG": "false", "PORT": "443", "SECRET_KEY": "prod-secret"}
ENV_LOCAL = {"DEBUG": "true", "LOG_LEVEL": "debug"}


def test_merge_non_overlapping_keys():
    result = merge_envs([("base", {"A": "1"}), ("extra", {"B": "2"})])
    assert result.merged == {"A": "1", "B": "2"}
    assert not result.has_conflicts


def test_merge_identical_values_no_conflict():
    result = merge_envs([("base", ENV_BASE), ("prod", ENV_PROD)])
    # DEBUG is same in both — no conflict
    conflict_keys = [c.key for c in result.conflicts]
    assert "DEBUG" not in conflict_keys


def test_merge_detects_conflict_on_differing_values():
    result = merge_envs([("base", ENV_BASE), ("prod", ENV_PROD)])
    conflict_keys = [c.key for c in result.conflicts]
    assert "PORT" in conflict_keys


def test_merge_override_mode_last_wins():
    result = merge_envs([("base", ENV_BASE), ("prod", ENV_PROD)], override=True)
    assert result.merged["PORT"] == "443"
    assert not result.has_conflicts


def test_merge_override_first_then_second_then_third():
    a = {"X": "1"}
    b = {"X": "2"}
    c = {"X": "3"}
    result = merge_envs([("a", a), ("b", b), ("c", c)], override=True)
    assert result.merged["X"] == "3"


def test_merge_ignore_conflicts_first_wins():
    result = merge_envs(
        [("base", ENV_BASE), ("prod", ENV_PROD)], ignore_conflicts=True
    )
    assert result.merged["PORT"] == "8080"
    assert not result.has_conflicts


def test_merge_three_sources_conflict_accumulates():
    a = {"KEY": "v1"}
    b = {"KEY": "v2"}
    c = {"KEY": "v3"}
    result = merge_envs([("a", a), ("b", b), ("c", c)])
    assert result.has_conflicts
    conflict = result.conflicts[0]
    assert conflict.key == "KEY"
    assert len(conflict.values) == 3


def test_merge_result_sources_recorded():
    result = merge_envs([("base", ENV_BASE), ("local", ENV_LOCAL)])
    assert result.sources == ["base", "local"]


def test_merge_summary_no_conflicts():
    result = merge_envs([("a", {"X": "1"}), ("b", {"Y": "2"})])
    summary = result.summary()
    assert "No conflicts" in summary
    assert "2" in summary  # total keys


def test_merge_summary_with_conflicts():
    result = merge_envs([("base", ENV_BASE), ("prod", ENV_PROD)])
    summary = result.summary()
    assert "Conflicts" in summary
    assert "PORT" in summary


def test_conflict_str_representation():
    conflict = MergeConflict(key="PORT", values=[("base", "8080"), ("prod", "443")])
    text = str(conflict)
    assert "PORT" in text
    assert "base" in text
    assert "8080" in text
    assert "prod" in text
    assert "443" in text
