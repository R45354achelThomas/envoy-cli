"""Tests for envoy.cli_pin."""

import json
from io import StringIO
from pathlib import Path

import pytest

from envoy.cli_pin import run_pin, build_parser


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("APP=myapp\nDB_HOST=localhost\nSECRET_KEY=abc123\n")
    return str(p)


def _run(argv, out=None, err=None):
    out = out or StringIO()
    err = err or StringIO()
    parser = build_parser()
    args = parser.parse_args(argv)
    code = run_pin(args, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_run_pin_creates_pin_file(env_file, tmp_path):
    pin_path = str(tmp_path / "my.pin.json")
    code, out, _ = _run([env_file, "--pin-file", pin_path])
    assert code == 0
    assert Path(pin_path).exists()


def test_run_pin_file_contains_keys(env_file, tmp_path):
    pin_path = str(tmp_path / "my.pin.json")
    _run([env_file, "--pin-file", pin_path])
    data = json.loads(Path(pin_path).read_text())
    assert data["APP"] == "myapp"
    assert data["DB_HOST"] == "localhost"


def test_run_pin_exits_zero_when_no_drift(env_file, tmp_path):
    pin_path = str(tmp_path / "my.pin.json")
    _run([env_file, "--pin-file", pin_path])  # create
    code, _, _ = _run([env_file, "--pin-file", pin_path])  # compare
    assert code == 0


def test_run_pin_exits_one_on_drift(env_file, tmp_path):
    pin_path = tmp_path / "my.pin.json"
    # Write a pin with a different value
    pin_path.write_text(json.dumps({"APP": "other", "DB_HOST": "localhost", "SECRET_KEY": "abc123"}))
    code, out, _ = _run([env_file, "--pin-file", str(pin_path)])
    assert code == 1
    assert "DRIFTED" in out


def test_run_pin_missing_key_reported(env_file, tmp_path):
    pin_path = tmp_path / "my.pin.json"
    pin_path.write_text(json.dumps({"APP": "myapp", "DB_HOST": "localhost",
                                     "SECRET_KEY": "abc123", "GONE": "old"}))
    code, out, _ = _run([env_file, "--pin-file", str(pin_path)])
    assert "MISSING" in out


def test_run_pin_new_keys_reported(env_file, tmp_path):
    pin_path = tmp_path / "my.pin.json"
    pin_path.write_text(json.dumps({"APP": "myapp"}))  # subset
    _, out, _ = _run([env_file, "--pin-file", str(pin_path)])
    assert "NEW" in out


def test_run_pin_bad_env_file_returns_one(tmp_path):
    code, _, err = _run([str(tmp_path / "nope.env")])
    assert code == 1
    assert "error" in err
