"""Tests for envoy.cli_filter.run_filter."""

import io
import textwrap
from pathlib import Path

import pytest

from envoy.cli_filter import run_filter


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        textwrap.dedent("""\
            DB_HOST=localhost
            DB_PORT=5432
            REDIS_URL=redis://localhost
            SECRET_KEY=abc123
            EMPTY_VAR=
        """)
    )
    return str(p)


def _run(env_file, **kwargs):
    out = io.StringIO()
    err = io.StringIO()
    code = run_filter(env_file, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


def test_run_filter_exits_zero(env_file):
    code, _, _ = _run(env_file)
    assert code == 0


def test_run_filter_prints_all_keys_by_default(env_file):
    _, out, _ = _run(env_file)
    assert "DB_HOST=localhost" in out
    assert "REDIS_URL=redis://localhost" in out


def test_run_filter_prefix_limits_output(env_file):
    _, out, _ = _run(env_file, prefix="DB_")
    assert "DB_HOST=localhost" in out
    assert "DB_PORT=5432" in out
    assert "REDIS_URL" not in out


def test_run_filter_pattern_limits_output(env_file):
    _, out, _ = _run(env_file, pattern="^SECRET")
    assert "SECRET_KEY=abc123" in out
    assert "DB_HOST" not in out


def test_run_filter_exclude_empty_drops_blank(env_file):
    _, out, _ = _run(env_file, exclude_empty=True)
    assert "EMPTY_VAR" not in out


def test_run_filter_invert_shows_non_db_keys(env_file):
    _, out, _ = _run(env_file, prefix="DB_", invert=True)
    assert "REDIS_URL" in out
    assert "DB_HOST" not in out


def test_run_filter_writes_to_output_file(env_file, tmp_path):
    out_path = str(tmp_path / "filtered.env")
    code, stdout, _ = _run(env_file, prefix="DB_", output=out_path)
    assert code == 0
    content = Path(out_path).read_text()
    assert "DB_HOST=localhost" in content
    assert "matched" in stdout


def test_run_filter_invalid_pattern_exits_nonzero(env_file):
    code, _, err = _run(env_file, pattern="[invalid")
    assert code == 1
    assert "Filter error" in err


def test_run_filter_missing_file_exits_nonzero(tmp_path):
    code, _, err = _run(str(tmp_path / "missing.env"))
    assert code == 1
    assert "Error loading" in err
