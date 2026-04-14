"""Integration tests for envoy.cli_rename.run_rename."""
import json
from pathlib import Path

import pytest

from envoy.cli_rename import run_rename


@pytest.fixture
def env_file(tmp_path: Path) -> str:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_SECRET=topsecret\n", encoding="utf-8")
    return str(p)


def test_run_rename_exits_zero(env_file, capsys):
    rc = run_rename(env_file, ["DB_HOST=DATABASE_HOST"], quiet=True)
    assert rc == 0


def test_run_rename_prints_renamed_key(env_file, capsys):
    run_rename(env_file, ["DB_HOST=DATABASE_HOST"])
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "DATABASE_HOST" in out


def test_run_rename_writes_output_file(env_file, tmp_path, capsys):
    out_path = str(tmp_path / "result.env")
    rc = run_rename(env_file, ["DB_HOST=DATABASE_HOST"], output=out_path, quiet=True)
    assert rc == 0
    content = Path(out_path).read_text(encoding="utf-8")
    assert "DATABASE_HOST" in content
    assert "DB_HOST" not in content


def test_run_rename_in_place(env_file, capsys):
    rc = run_rename(env_file, ["DB_HOST=DATABASE_HOST"], in_place=True, quiet=True)
    assert rc == 0
    content = Path(env_file).read_text(encoding="utf-8")
    assert "DATABASE_HOST" in content
    assert "DB_HOST" not in content


def test_run_rename_missing_source_exits_one(tmp_path, capsys):
    rc = run_rename(str(tmp_path / "nope.env"), ["A=B"])
    assert rc == 1
    assert "error" in capsys.readouterr().err.lower()


def test_run_rename_bad_spec_exits_one(env_file, capsys):
    rc = run_rename(env_file, ["NOEQUALSSIGN"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "OLD=NEW" in err


def test_run_rename_skipped_shown_in_output(env_file, capsys):
    run_rename(env_file, ["MISSING_KEY=NEW_KEY"])
    out = capsys.readouterr().out
    assert "skipped" in out


def test_run_rename_no_overwrite_by_default(env_file, capsys):
    # DB_PORT already exists; rename DB_HOST -> DB_PORT should be skipped
    rc = run_rename(env_file, ["DB_HOST=DB_PORT"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "skipped" in out


def test_run_rename_allow_overwrite(env_file, tmp_path, capsys):
    out_path = str(tmp_path / "result.env")
    rc = run_rename(
        env_file,
        ["DB_HOST=DB_PORT"],
        allow_overwrite=True,
        output=out_path,
        quiet=True,
    )
    assert rc == 0
    content = Path(out_path).read_text(encoding="utf-8")
    assert "DB_PORT=localhost" in content
