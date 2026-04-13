"""Tests for envoy.cli_audit."""
import io

import pytest

import envoy.auditor as auditor
from envoy.cli_audit import run_audit, build_parser


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    log_file = tmp_path / "audit.jsonl"
    monkeypatch.setenv(auditor.AUDIT_LOG_ENV_VAR, str(log_file))
    monkeypatch.setenv("USER", "ci")
    yield log_file


def _capture(limit=20, action_filter=None):
    buf = io.StringIO()
    rc = run_audit(limit=limit, action_filter=action_filter, output=buf)
    return rc, buf.getvalue()


def test_empty_log_prints_message(isolated_log):
    rc, out = _capture()
    assert rc == 0
    assert "No audit entries found" in out


def test_single_entry_appears_in_output(isolated_log):
    auditor.record("load", "dev.env")
    rc, out = _capture()
    assert rc == 0
    assert "load" in out
    assert "dev.env" in out


def test_multiple_entries_all_shown(isolated_log):
    auditor.record("load", "a.env")
    auditor.record("diff", "b.env")
    auditor.record("export", "c.env")
    _, out = _capture()
    assert "load" in out
    assert "diff" in out
    assert "export" in out


def test_limit_restricts_output(isolated_log):
    for i in range(10):
        auditor.record("load", f"file{i}.env")
    _, out = _capture(limit=3)
    # header + separator + 3 entries = 5 lines
    lines = [l for l in out.strip().splitlines() if l.strip()]
    assert len(lines) == 5


def test_action_filter_shows_only_matching(isolated_log):
    auditor.record("load", "a.env")
    auditor.record("diff", "b.env")
    auditor.record("load", "c.env")
    _, out = _capture(action_filter="load")
    assert "diff" not in out
    assert out.count("load") >= 2


def test_action_filter_no_match_shows_message(isolated_log):
    auditor.record("load", "a.env")
    _, out = _capture(action_filter="merge")
    assert "No audit entries found" in out


def test_details_shown_in_output(isolated_log):
    auditor.record("export", "prod.env", details={"format": "json"})
    _, out = _capture()
    assert "format=json" in out


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])
    assert args.limit == 20
    assert args.action is None
