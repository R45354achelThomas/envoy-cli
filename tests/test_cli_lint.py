"""Tests for envoy.cli_lint."""
import io
import pytest
from pathlib import Path

from envoy.cli_lint import run_lint, build_parser


@pytest.fixture
def clean_env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\n")
    return p


@pytest.fixture
def dirty_env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("db_host=localhost\nDB_HOST=remotehost\nDB_HOST=other\n")
    return p


def test_clean_file_exits_zero(clean_env_file):
    out = io.StringIO()
    code = run_lint(str(clean_env_file), output=out)
    assert code == 0


def test_clean_file_prints_no_issues(clean_env_file):
    out = io.StringIO()
    run_lint(str(clean_env_file), output=out)
    assert "No lint issues found" in out.getvalue()


def test_dirty_file_with_error_exits_one(dirty_env_file):
    out = io.StringIO()
    code = run_lint(str(dirty_env_file), output=out)
    assert code == 1


def test_dirty_file_prints_L003(dirty_env_file):
    out = io.StringIO()
    run_lint(str(dirty_env_file), output=out)
    assert "L003" in out.getvalue()


def test_no_warnings_flag_suppresses_warnings(dirty_env_file):
    out = io.StringIO()
    run_lint(str(dirty_env_file), show_warnings=False, output=out)
    # L001 is a warning and should be absent
    assert "L001" not in out.getvalue()


def test_strict_mode_exits_one_on_warnings_only(tmp_path):
    p = tmp_path / ".env"
    p.write_text("db_host=localhost\n")  # only warning, no error
    out = io.StringIO()
    code = run_lint(str(p), strict=True, output=out)
    assert code == 1


def test_strict_mode_off_exits_zero_on_warnings_only(tmp_path):
    p = tmp_path / ".env"
    p.write_text("db_host=localhost\n")
    out = io.StringIO()
    code = run_lint(str(p), strict=False, output=out)
    assert code == 0


def test_missing_file_exits_with_code(tmp_path):
    with pytest.raises(SystemExit) as exc_info:
        run_lint(str(tmp_path / "nonexistent.env"))
    assert exc_info.value.code == 2


def test_build_parser_returns_parser():
    parser = build_parser()
    args = parser.parse_args(["my.env", "--strict"])
    assert args.env_file == "my.env"
    assert args.strict is True
    assert args.no_warnings is False
