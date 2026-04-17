import pytest
from io import StringIO
from pathlib import Path
from envoy.cli_score import run_score, build_parser


@pytest.fixture
def clean_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text("DATABASE_URL=postgres://localhost/db\nPORT=8080\n")
    return str(f)


@pytest.fixture
def dirty_env_file(tmp_path):
    f = tmp_path / ".env.dirty"
    f.write_text("api_secret=changeme\nTOKEN=\n")
    return str(f)


def _run(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    out, err = StringIO(), StringIO()
    code = run_score(args, out=out, err=err)
    return code, out.getvalue(), err.getvalue()


def test_clean_file_exits_zero(clean_env_file):
    code, _, _ = _run([clean_env_file])
    assert code == 0


def test_clean_file_prints_score_100(clean_env_file):
    _, out, _ = _run([clean_env_file])
    assert "100" in out


def test_dirty_file_shows_issues(dirty_env_file):
    _, out, _ = _run([dirty_env_file])
    assert "issue" in out.lower() or "ERROR" in out or "WARNING" in out


def test_min_score_pass(clean_env_file):
    code, _, _ = _run([clean_env_file, "--min-score", "80"])
    assert code == 0


def test_min_score_fail(dirty_env_file):
    code, _, err = _run([dirty_env_file, "--min-score", "99"])
    assert code == 1
    assert "below minimum" in err


def test_summary_line_present(clean_env_file):
    _, out, _ = _run([clean_env_file])
    assert "Score:" in out
