"""Unit tests for envoy.parser."""

import pytest
from envoy.parser import parse_env_string, serialize_env, EnvParseError


SAMPLE = """
# Database settings
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD="s3cr3t#word"
export APP_ENV=production
DEBUG=false  # inline comment
QUOTED_SINGLE='hello world'
EMPTY_VAL=
"""


def test_basic_parsing():
    env = parse_env_string(SAMPLE)
    assert env["DB_HOST"] == "localhost"
    assert env["DB_PORT"] == "5432"
    assert env["APP_ENV"] == "production"


def test_double_quoted_value():
    env = parse_env_string(SAMPLE)
    assert env["DB_PASSWORD"] == "s3cr3t#word"


def test_single_quoted_value():
    env = parse_env_string(SAMPLE)
    assert env["QUOTED_SINGLE"] == "hello world"


def test_inline_comment_stripped():
    env = parse_env_string(SAMPLE)
    assert env["DEBUG"] == "false"


def test_empty_value():
    env = parse_env_string(SAMPLE)
    assert env["EMPTY_VAL"] == ""


def test_comments_and_blank_lines_ignored():
    env = parse_env_string(SAMPLE)
    assert all(not k.startswith("#") for k in env)


def test_export_prefix_stripped():
    env = parse_env_string("export FOO=bar")
    assert "FOO" in env
    assert env["FOO"] == "bar"


def test_strict_mode_raises_on_invalid_line():
    bad = "THIS IS NOT VALID\nGOOD=ok\n"
    with pytest.raises(EnvParseError) as exc_info:
        parse_env_string(bad, strict=True)
    assert exc_info.value.line_number == 1


def test_non_strict_skips_invalid_line():
    bad = "THIS IS NOT VALID\nGOOD=ok\n"
    env = parse_env_string(bad, strict=False)
    assert env == {"GOOD": "ok"}


def test_serialize_roundtrip():
    original = {"HOST": "localhost", "MSG": 'say "hi"', "PLAIN": "value"}
    serialized = serialize_env(original)
    from envoy.parser import parse_env_string as p
    recovered = p(serialized)
    assert recovered["HOST"] == "localhost"
    assert recovered["MSG"] == 'say "hi"'
    assert recovered["PLAIN"] == "value"
