"""Tests for envoy.cli_export module."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from envoy.cli_export import run_export


SAMPLE_ENV = {"APP": "test", "PORT": "9000"}


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("APP=test\nPORT=9000\n")
    return f


def test_run_export_prints_dotenv(env_file, capsys):
    run_export(str(env_file), fmt="dotenv")
    captured = capsys.readouterr()
    assert "APP=test" in captured.out
    assert "PORT=9000" in captured.out


def test_run_export_prints_json(env_file, capsys):
    run_export(str(env_file), fmt="json")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["APP"] == "test"
    assert data["PORT"] == "9000"


def test_run_export_prints_shell(env_file, capsys):
    run_export(str(env_file), fmt="shell")
    captured = capsys.readouterr()
    assert 'export APP="test"' in captured.out


def test_run_export_writes_to_file(env_file, tmp_path, capsys):
    out_file = tmp_path / "output.json"
    run_export(str(env_file), fmt="json", output=str(out_file))
    assert out_file.exists()
    data = json.loads(out_file.read_text())
    assert data["APP"] == "test"
    captured = capsys.readouterr()
    assert "Exported" in captured.out


def test_run_export_exits_on_missing_file():
    with pytest.raises(SystemExit) as exc_info:
        run_export("/nonexistent/.env", fmt="json")
    assert exc_info.value.code == 1


def test_run_export_exits_on_unknown_format(env_file):
    with pytest.raises(SystemExit) as exc_info:
        run_export(str(env_file), fmt="xml")  # type: ignore
    assert exc_info.value.code == 1
