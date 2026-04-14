"""Tests for envoy.comparator."""

from __future__ import annotations

import pytest

from envoy.comparator import compare, ComparisonReport


BASE = {
    "APP_NAME": "myapp",
    "DB_HOST": "localhost",
    "SECRET_KEY": "old-secret",
    "LOG_LEVEL": "debug",
}

TARGET = {
    "APP_NAME": "myapp",
    "DB_HOST": "prod.db.example.com",
    "SECRET_KEY": "new-secret",
    "NEW_FEATURE_FLAG": "true",
}


@pytest.fixture
def report() -> ComparisonReport:
    return compare(BASE, TARGET, base_path="base.env", target_path="target.env", include_lint=False)


def test_report_has_correct_paths(report):
    assert report.base_path == "base.env"
    assert report.target_path == "target.env"


def test_added_keys_detected(report):
    keys = [e.key for e in report.added]
    assert "NEW_FEATURE_FLAG" in keys


def test_removed_keys_detected(report):
    keys = [e.key for e in report.removed]
    assert "LOG_LEVEL" in keys


def test_changed_keys_detected(report):
    keys = [e.key for e in report.changed]
    assert "DB_HOST" in keys


def test_unchanged_key_not_in_diff(report):
    all_keys = [e.key for e in report.diff_entries]
    assert "APP_NAME" not in all_keys


def test_secret_key_change_detected(report):
    keys = [e.key for e in report.changed]
    assert "SECRET_KEY" in keys


def test_summary_contains_counts(report):
    s = report.summary()
    assert "Added" in s
    assert "Removed" in s
    assert "Changed" in s


def test_no_lint_when_disabled(report):
    assert report.base_lint is None
    assert report.target_lint is None


def test_no_validation_when_no_schema(report):
    assert report.base_validation is None
    assert report.target_validation is None


def test_has_lint_errors_false_when_no_lint(report):
    assert report.has_lint_errors is False


def test_identical_envs_produce_empty_diff():
    r = compare(BASE, BASE, include_lint=False)
    assert r.diff_entries == []


def test_empty_base_all_added():
    r = compare({}, TARGET, include_lint=False)
    assert len(r.added) == len(TARGET)
    assert r.removed == []
    assert r.changed == []


def test_empty_target_all_removed():
    r = compare(BASE, {}, include_lint=False)
    assert len(r.removed) == len(BASE)
    assert r.added == []
    assert r.changed == []
