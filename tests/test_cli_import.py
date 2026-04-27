"""Tests for envoy.cli_import."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.cli_import import build_parser, run_import


@pytest.fixture()
def json_file(tmp_path: Path) -> Path:
    data = {"HOST": "db.local", "PORT": "5432", "SECRET_KEY": "abc123"}
    p = tmp_path / "vars.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


@pytest.fixture()
def dotenv_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("HOST=localhost\nPORT=3000\n", encoding="utf-8")
    return p


def _run(argv, capsys=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    code = run_import(args)
    return code


# ---------------------------------------------------------------------------
# json source
# ---------------------------------------------------------------------------

def test_json_source_exits_zero(json_file, capsys):
    code = _run(["json", "--file", str(json_file), "--quiet"])
    assert code == 0


def test_json_source_prints_dotenv(json_file, capsys):
    parser = build_parser()
    args = parser.parse_args(["json", "--file", str(json_file), "--quiet"])
    run_import(args)
    out = capsys.readouterr().out
    assert "HOST=" in out
    assert "PORT=" in out


def test_json_source_key_filter(json_file, capsys):
    parser = build_parser()
    args = parser.parse_args(["json", "--file", str(json_file), "--keys", "HOST", "--quiet"])
    run_import(args)
    out = capsys.readouterr().out
    assert "HOST=" in out
    assert "PORT" not in out


def test_json_source_writes_output_file(json_file, tmp_path):
    out_file = tmp_path / "result.env"
    _run(["json", "--file", str(json_file), "--output", str(out_file), "--quiet"])
    content = out_file.read_text()
    assert "HOST=" in content


def test_json_source_missing_file_returns_one(tmp_path):
    code = _run(["json", "--file", str(tmp_path / "missing.json"), "--quiet"])
    assert code == 1


def test_json_source_no_file_arg_returns_two():
    code = _run(["json", "--quiet"])
    assert code == 2


# ---------------------------------------------------------------------------
# dotenv source
# ---------------------------------------------------------------------------

def test_dotenv_source_exits_zero(dotenv_file):
    code = _run(["dotenv", "--file", str(dotenv_file), "--quiet"])
    assert code == 0


def test_dotenv_source_prints_keys(dotenv_file, capsys):
    parser = build_parser()
    args = parser.parse_args(["dotenv", "--file", str(dotenv_file), "--quiet"])
    run_import(args)
    out = capsys.readouterr().out
    assert "HOST=" in out
    assert "PORT=" in out


# ---------------------------------------------------------------------------
# shell source
# ---------------------------------------------------------------------------

def test_shell_source_exits_zero(monkeypatch):
    monkeypatch.setenv("ENVOY_TEST_VAR", "hello")
    code = _run(["shell", "--keys", "ENVOY_TEST_VAR", "--quiet"])
    assert code == 0


def test_shell_source_prefix_filter(monkeypatch, capsys):
    monkeypatch.setenv("MYAPP_HOST", "localhost")
    parser = build_parser()
    args = parser.parse_args(["shell", "--prefix", "MYAPP_", "--quiet"])
    run_import(args)
    out = capsys.readouterr().out
    assert "MYAPP_HOST=" in out


def test_shell_source_strip_prefix(monkeypatch, capsys):
    monkeypatch.setenv("MYAPP_HOST", "localhost")
    parser = build_parser()
    args = parser.parse_args(["shell", "--prefix", "MYAPP_", "--strip-prefix", "--quiet"])
    run_import(args)
    out = capsys.readouterr().out
    assert "HOST=" in out
    assert "MYAPP_HOST" not in out
