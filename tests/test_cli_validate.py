"""Tests for envoy.cli_validate."""

from __future__ import annotations

import io
import textwrap

import pytest

from envoy.cli_validate import run_validate


@pytest.fixture()
def schema_file(tmp_path):
    f = tmp_path / "schema.env"
    f.write_text(
        textwrap.dedent("""\
        DATABASE_URL=postgres://localhost/db
        SECRET_KEY=changeme
        DEBUG=false
        """)
    )
    return str(f)


@pytest.fixture()
def valid_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        textwrap.dedent("""\
        DATABASE_URL=postgres://prod/db
        SECRET_KEY=supersecret
        DEBUG=false
        """)
    )
    return str(f)


@pytest.fixture()
def missing_key_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        textwrap.dedent("""\
        DATABASE_URL=postgres://prod/db
        """)
    )
    return str(f)


@pytest.fixture()
def extra_key_env_file(tmp_path):
    f = tmp_path / ".env"
    f.write_text(
        textwrap.dedent("""\
        DATABASE_URL=postgres://prod/db
        SECRET_KEY=supersecret
        DEBUG=false
        EXTRA_KEY=oops
        """)
    )
    return str(f)


def test_valid_env_exits_zero(valid_env_file, schema_file):
    out = io.StringIO()
    code = run_validate(valid_env_file, schema_file, output=out)
    assert code == 0


def test_valid_env_prints_ok(valid_env_file, schema_file):
    out = io.StringIO()
    run_validate(valid_env_file, schema_file, output=out)
    assert "OK" in out.getvalue()


def test_missing_key_exits_nonzero(missing_key_env_file, schema_file):
    out = io.StringIO()
    code = run_validate(missing_key_env_file, schema_file, output=out)
    assert code == 1


def test_missing_key_mentioned_in_output(missing_key_env_file, schema_file):
    out = io.StringIO()
    run_validate(missing_key_env_file, schema_file, output=out)
    assert "SECRET_KEY" in out.getvalue() or "DEBUG" in out.getvalue()


def test_extra_key_non_strict_exits_zero(extra_key_env_file, schema_file):
    out = io.StringIO()
    code = run_validate(extra_key_env_file, schema_file, strict=False, output=out)
    assert code == 0


def test_extra_key_strict_exits_nonzero(extra_key_env_file, schema_file):
    out = io.StringIO()
    code = run_validate(extra_key_env_file, schema_file, strict=True, output=out)
    assert code == 1
