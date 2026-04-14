"""Tests for envoy.cli_patch."""

import io
import pytest
from pathlib import Path
from envoy.cli_patch import run_patch, build_parser, _parse_assignments


SAMPLE = "APP_ENV=staging\nDB_HOST=localhost\nDB_PORT=5432\n"


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(SAMPLE, encoding="utf-8")
    return p


def _run(env_file, assignments, **kwargs):
    out = io.StringIO()
    err = io.StringIO()
    code = run_patch(env_file, assignments, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


def test_run_patch_updates_key(env_file):
    code, out, _ = _run(env_file, {"DB_HOST": "prod.db"})
    assert code == 0
    assert "DB_HOST=prod.db" in env_file.read_text()


def test_run_patch_prints_summary(env_file):
    code, out, _ = _run(env_file, {"DB_HOST": "x"})
    assert "updated" in out


def test_run_patch_adds_new_key(env_file):
    code, out, _ = _run(env_file, {"NEW_KEY": "new_val"})
    assert code == 0
    content = env_file.read_text()
    assert "NEW_KEY=new_val" in content
    assert "added" in out


def test_run_patch_no_add_flag(env_file):
    code, out, _ = _run(env_file, {"GHOST": "x"}, add_missing=False)
    assert code == 0
    assert "GHOST" not in env_file.read_text()


def test_run_patch_quiet_suppresses_output(env_file):
    code, out, _ = _run(env_file, {"DB_PORT": "9999"}, quiet=True)
    assert code == 0
    assert out == ""


def test_run_patch_missing_file_returns_error(tmp_path):
    code, _, err = _run(tmp_path / "ghost.env", {"KEY": "val"})
    assert code == 1
    assert "error" in err.lower()


def test_parse_assignments_valid():
    result = _parse_assignments(["FOO=bar", "BAZ=qux"])
    assert result == {"FOO": "bar", "BAZ": "qux"}


def test_parse_assignments_value_with_equals():
    result = _parse_assignments(["URL=http://x.com/path?a=1"])
    assert result["URL"] == "http://x.com/path?a=1"


def test_parse_assignments_missing_equals_raises():
    import argparse
    with pytest.raises(argparse.ArgumentTypeError):
        _parse_assignments(["NOEQUALS"])


def test_build_parser_defaults():
    p = build_parser()
    args = p.parse_args([".env", "KEY=val"])
    assert args.add_missing is True
    assert args.preserve_quotes is False
    assert args.quiet is False


def test_build_parser_no_add_flag():
    p = build_parser()
    args = p.parse_args([".env", "KEY=val", "--no-add"])
    assert args.add_missing is False


def test_build_parser_preserve_quotes_flag():
    p = build_parser()
    args = p.parse_args([".env", "KEY=val", "--preserve-quotes"])
    assert args.preserve_quotes is True
