"""Tests for envoy.cli_group."""
import json
import io
import textwrap
from pathlib import Path

import pytest

from envoy.cli_group import run_group


@pytest.fixture
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text(
        textwrap.dedent("""\
            DB_HOST=localhost
            DB_PORT=5432
            REDIS_URL=redis://localhost
            PORT=8080
        """)
    )
    return str(p)


def _run(env_file, **kwargs):
    out = io.StringIO()
    err = io.StringIO()
    code = run_group(env_file, out=out, err=err, **kwargs)
    return code, out.getvalue(), err.getvalue()


def test_run_group_exits_zero(env_file):
    code, _, _ = _run(env_file)
    assert code == 0


def test_run_group_text_shows_db_group(env_file):
    _, out, _ = _run(env_file)
    assert "[DB]" in out
    assert "DB_HOST=localhost" in out


def test_run_group_text_shows_redis_group(env_file):
    _, out, _ = _run(env_file)
    assert "[REDIS]" in out


def test_run_group_text_shows_ungrouped(env_file):
    _, out, _ = _run(env_file, show_ungrouped=True)
    assert "[ungrouped]" in out
    assert "PORT=8080" in out


def test_run_group_no_ungrouped_hides_section(env_file):
    _, out, _ = _run(env_file, show_ungrouped=False)
    assert "[ungrouped]" not in out


def test_run_group_json_format(env_file):
    code, out, _ = _run(env_file, output_format="json")
    assert code == 0
    data = json.loads(out)
    assert "groups" in data
    assert "DB" in data["groups"]


def test_run_group_json_includes_ungrouped(env_file):
    _, out, _ = _run(env_file, output_format="json", show_ungrouped=True)
    data = json.loads(out)
    assert "ungrouped" in data
    assert "PORT" in data["ungrouped"]


def test_run_group_summary_printed_to_stderr(env_file):
    _, _, err = _run(env_file)
    assert "DB" in err or "key" in err


def test_run_group_missing_file_exits_one(tmp_path):
    code, _, err = _run(str(tmp_path / "missing.env"))
    assert code == 1
    assert "error" in err.lower()


def test_run_group_prefix_map_file(env_file, tmp_path):
    pm = tmp_path / "map.json"
    pm.write_text(json.dumps({"DB": "database", "REDIS": "cache"}))
    code, out, _ = _run(env_file, prefix_map_path=str(pm), output_format="json")
    assert code == 0
    data = json.loads(out)
    assert "database" in data["groups"]
    assert "cache" in data["groups"]
