"""Tests for envoy.auditor."""
import json
from pathlib import Path

import pytest

import envoy.auditor as auditor


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    log_file = tmp_path / "test_audit.jsonl"
    monkeypatch.setenv(auditor.AUDIT_LOG_ENV_VAR, str(log_file))
    monkeypatch.setenv("USER", "test_user")
    yield log_file


def test_record_creates_log_file(isolated_log):
    auditor.record("load", ".env")
    assert isolated_log.exists()


def test_record_returns_audit_entry(isolated_log):
    entry = auditor.record("diff", "old.env")
    assert entry.action == "diff"
    assert entry.target == "old.env"
    assert entry.user == "test_user"


def test_record_writes_valid_jsonl(isolated_log):
    auditor.record("export", "prod.env", details={"format": "json"})
    lines = isolated_log.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["action"] == "export"
    assert data["details"]["format"] == "json"


def test_record_multiple_entries(isolated_log):
    auditor.record("load", "a.env")
    auditor.record("merge", "b.env")
    auditor.record("snapshot", "snap1")
    lines = isolated_log.read_text().strip().splitlines()
    assert len(lines) == 3


def test_read_log_empty_when_no_file(isolated_log):
    entries = auditor.read_log()
    assert entries == []


def test_read_log_returns_all_entries(isolated_log):
    auditor.record("load", "x.env")
    auditor.record("diff", "y.env")
    entries = auditor.read_log()
    assert len(entries) == 2
    assert entries[0].action == "load"
    assert entries[1].action == "diff"


def test_read_log_limit(isolated_log):
    for i in range(5):
        auditor.record("load", f"file{i}.env")
    entries = auditor.read_log(limit=3)
    assert len(entries) == 3
    assert entries[-1].target == "file4.env"


def test_timestamp_is_iso_format(isolated_log):
    entry = auditor.record("load", ".env")
    # Should not raise
    from datetime import datetime
    datetime.fromisoformat(entry.timestamp)


def test_details_default_empty_dict(isolated_log):
    entry = auditor.record("load", ".env")
    assert entry.details == {}
