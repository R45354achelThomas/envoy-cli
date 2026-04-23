"""Tests for envoy.cli_map."""
import json
from pathlib import Path

import pytest

from envoy.cli_map import build_parser, run_map


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=abc\n")
    return str(p)


@pytest.fixture
def mapping_file(tmp_path):
    m = tmp_path / "mapping.json"
    m.write_text(json.dumps({"DB_HOST": "DATABASE_HOST", "SECRET_KEY": None}))
    return str(m)


def _run(env_file, mapping, extra=None):
    parser = build_parser()
    argv = [env_file, mapping] + (extra or [])
    args = parser.parse_args(argv)
    return run_map(args)


def test_run_map_exits_zero(env_file, mapping_file):
    assert _run(env_file, mapping_file) == 0


def test_run_map_renames_key(env_file, mapping_file, capsys):
    _run(env_file, mapping_file)
    out = capsys.readouterr().out
    assert "DATABASE_HOST" in out
    assert "DB_HOST" not in out


def test_run_map_drops_none_key(env_file, mapping_file, capsys):
    _run(env_file, mapping_file)
    out = capsys.readouterr().out
    assert "SECRET_KEY" not in out


def test_run_map_preserves_unmapped_key(env_file, mapping_file, capsys):
    _run(env_file, mapping_file)
    out = capsys.readouterr().out
    assert "DB_PORT" in out


def test_run_map_drop_unmapped_excludes_other_keys(env_file, mapping_file, capsys):
    _run(env_file, mapping_file, ["--drop-unmapped"])
    out = capsys.readouterr().out
    assert "DB_PORT" not in out
    assert "DATABASE_HOST" in out


def test_run_map_writes_output_file(env_file, mapping_file, tmp_path):
    out_file = str(tmp_path / "out.env")
    _run(env_file, mapping_file, ["-o", out_file])
    content = Path(out_file).read_text()
    assert "DATABASE_HOST" in content


def test_run_map_missing_env_file_exits_two(mapping_file):
    code = _run("/no/such/.env", mapping_file)
    assert code == 2


def test_run_map_missing_mapping_file_exits_two(env_file):
    code = _run(env_file, "/no/such/mapping.json")
    assert code == 2


def test_run_map_invalid_mapping_json_exits_two(env_file, tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json")
    code = _run(env_file, str(bad))
    assert code == 2


def test_run_map_quiet_suppresses_summary(env_file, mapping_file, capsys):
    _run(env_file, mapping_file, ["-q"])
    err = capsys.readouterr().err
    assert err == ""
