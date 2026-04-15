"""Tests for envoy.cli_normalize."""
import json
from pathlib import Path

import pytest

from envoy.cli_normalize import run_normalize


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("db_host=localhost\nAPI_KEY=  secret  \n", encoding="utf-8")
    return str(p)


@pytest.fixture
def already_normalized(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nAPI_KEY=secret\n", encoding="utf-8")
    return str(p)


def test_run_normalize_exits_zero(env_file):
    assert run_normalize(env_file) == 0


def test_run_normalize_uppercases_keys(env_file, tmp_path, capsys):
    out = tmp_path / "out.env"
    run_normalize(env_file, str(out))
    content = out.read_text()
    assert "DB_HOST" in content
    assert "db_host" not in content


def test_run_normalize_strips_values(env_file, tmp_path):
    out = tmp_path / "out.env"
    run_normalize(env_file, str(out))
    content = out.read_text()
    assert "secret" in content
    assert "  secret  " not in content


def test_run_normalize_prints_to_stdout(env_file, capsys):
    run_normalize(env_file)
    captured = capsys.readouterr()
    assert "DB_HOST" in captured.out


def test_run_normalize_summary_on_stderr(env_file, capsys):
    run_normalize(env_file)
    captured = capsys.readouterr()
    assert "normalized" in captured.err or "already" in captured.err


def test_run_normalize_quiet_suppresses_summary(env_file, capsys):
    run_normalize(env_file, quiet=True)
    captured = capsys.readouterr()
    assert captured.err == ""


def test_run_normalize_no_uppercase_preserves_case(env_file, tmp_path):
    out = tmp_path / "out.env"
    run_normalize(env_file, str(out), no_uppercase=True)
    content = out.read_text()
    assert "db_host" in content


def test_run_normalize_missing_file_exits_one():
    assert run_normalize("/nonexistent/.env") == 1


def test_run_normalize_already_normalized_reports_no_changes(already_normalized, capsys):
    run_normalize(already_normalized)
    captured = capsys.readouterr()
    assert "already normalized" in captured.err
