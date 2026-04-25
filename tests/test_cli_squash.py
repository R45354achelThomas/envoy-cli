"""Tests for envoy.cli_squash."""
import json
from pathlib import Path

import pytest

from envoy.cli_squash import run_squash, build_parser


@pytest.fixture()
def base_file(tmp_path):
    p = tmp_path / "base.env"
    p.write_text("HOST=localhost\nPORT=5432\nDEBUG=true\n")
    return str(p)


@pytest.fixture()
def override_file(tmp_path):
    p = tmp_path / "override.env"
    p.write_text("PORT=9999\nSECRET_KEY=abc123\n")
    return str(p)


def _run(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_squash(args)


def test_run_squash_exits_zero(base_file, override_file):
    assert _run([base_file, override_file]) == 0


def test_run_squash_last_wins_default(base_file, override_file, capsys):
    _run([base_file, override_file])
    out = capsys.readouterr().out
    assert "PORT=9999" in out


def test_run_squash_first_wins(base_file, override_file, capsys):
    _run(["--first-wins", base_file, override_file])
    out = capsys.readouterr().out
    assert "PORT=5432" in out


def test_run_squash_json_format(base_file, override_file, capsys):
    _run(["--format", "json", base_file, override_file])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["PORT"] == "9999"
    assert data["HOST"] == "localhost"


def test_run_squash_writes_output_file(base_file, override_file, tmp_path):
    out_file = str(tmp_path / "result.env")
    _run([base_file, override_file, "-o", out_file])
    content = Path(out_file).read_text()
    assert "PORT=9999" in content


def test_run_squash_verbose_prints_override_info(base_file, override_file, capsys):
    _run(["-v", base_file, override_file])
    err = capsys.readouterr().err
    assert "PORT" in err


def test_run_squash_missing_file_exits_one(tmp_path):
    assert _run([str(tmp_path / "nonexistent.env")]) == 1
