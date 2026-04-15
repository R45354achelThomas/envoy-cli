"""Tests for envoy.cli_strip."""

import pytest
from pathlib import Path
from envoy.cli_strip import run_strip


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "APP_SECRET=s3cr3t\n"
        "LOG_LEVEL=info\n"
    )
    return str(p)


def _run(env_file, **kwargs):
    """Helper: run_strip capturing stdout via output file."""
    import tempfile, os
    with tempfile.NamedTemporaryFile(mode="r", suffix=".env", delete=False) as f:
        out = f.name
    try:
        code = run_strip(env_file, output=out, quiet=True, **kwargs)
        content = Path(out).read_text()
    finally:
        os.unlink(out)
    return code, content


def test_run_strip_exits_zero(env_file):
    code, _ = _run(env_file)
    assert code == 0


def test_run_strip_exact_key_removed(env_file):
    _, content = _run(env_file, keys=["LOG_LEVEL"])
    assert "LOG_LEVEL" not in content


def test_run_strip_other_keys_preserved(env_file):
    _, content = _run(env_file, keys=["LOG_LEVEL"])
    assert "DB_HOST" in content
    assert "APP_SECRET" in content


def test_run_strip_prefix_removes_db_keys(env_file):
    _, content = _run(env_file, prefix="DB_")
    assert "DB_HOST" not in content
    assert "DB_PORT" not in content
    assert "LOG_LEVEL" in content


def test_run_strip_pattern_removes_matching(env_file):
    _, content = _run(env_file, patterns=[r"^APP_"])
    assert "APP_SECRET" not in content
    assert "DB_HOST" in content


def test_run_strip_prints_summary(env_file, capsys):
    run_strip(env_file, keys=["LOG_LEVEL"], output=None, quiet=False)
    captured = capsys.readouterr()
    assert "LOG_LEVEL" in captured.err


def test_run_strip_quiet_suppresses_summary(env_file, capsys):
    run_strip(env_file, keys=["LOG_LEVEL"], output=None, quiet=True)
    captured = capsys.readouterr()
    assert captured.err == ""
