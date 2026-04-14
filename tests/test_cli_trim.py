"""Tests for envoy.cli_trim."""

import pytest
from pathlib import Path

from envoy.cli_trim import run_trim


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("KEY_A=  hello  \nKEY_B=world\n", encoding="utf-8")
    return str(p)


@pytest.fixture
def dirty_env_file(tmp_path):
    p = tmp_path / "dirty.env"
    p.write_text("  KEY_X  =  value  \nKEY_Y=clean\n", encoding="utf-8")
    return str(p)


def test_run_trim_exits_zero(env_file):
    code = run_trim(env_file, quiet=True)
    assert code == 0


def test_run_trim_prints_to_stdout(env_file, capsys):
    run_trim(env_file, quiet=True)
    out = capsys.readouterr().out
    assert "KEY_A" in out
    assert "hello" in out


def test_run_trim_strips_value_whitespace(env_file, capsys):
    run_trim(env_file, quiet=True)
    out = capsys.readouterr().out
    assert "  hello  " not in out
    assert "hello" in out


def test_run_trim_writes_to_output_file(env_file, tmp_path):
    out_path = str(tmp_path / "out.env")
    run_trim(env_file, output_path=out_path, quiet=True)
    content = Path(out_path).read_text(encoding="utf-8")
    assert "hello" in content
    assert "  hello  " not in content


def test_run_trim_in_place_overwrites_input(env_file):
    run_trim(env_file, in_place=True, quiet=True)
    content = Path(env_file).read_text(encoding="utf-8")
    assert "  hello  " not in content
    assert "hello" in content


def test_run_trim_summary_printed_to_stderr(env_file, capsys):
    run_trim(env_file)
    err = capsys.readouterr().err
    assert "Trimmed" in err or "No changes" in err


def test_run_trim_quiet_suppresses_summary(env_file, capsys):
    run_trim(env_file, quiet=True)
    err = capsys.readouterr().err
    assert err == ""


def test_run_trim_no_strip_values_preserves_whitespace(env_file, capsys):
    run_trim(env_file, no_strip_values=True, quiet=True)
    out = capsys.readouterr().out
    assert "  hello  " in out
