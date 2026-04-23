"""Tests for envoy/coercer.py."""

import pytest

from envoy.coercer import CoerceError, CoerceResult, coerce


@pytest.fixture()
def sample_env():
    return {
        "PORT": "8080",
        "TIMEOUT": "3.14",
        "DEBUG": "true",
        "NAME": "envoy",
        "RETRIES": "bad_int",
    }


def test_coerce_returns_coerce_result(sample_env):
    result = coerce(sample_env, {})
    assert isinstance(result, CoerceResult)


def test_no_schema_leaves_all_strings(sample_env):
    result = coerce(sample_env, {})
    assert result.env["PORT"] == "8080"
    assert result.coerced_keys == []
    assert not result.has_issues()


def test_int_coercion(sample_env):
    result = coerce(sample_env, {"PORT": "int"})
    assert result.env["PORT"] == 8080
    assert isinstance(result.env["PORT"], int)
    assert "PORT" in result.coerced_keys


def test_float_coercion(sample_env):
    result = coerce(sample_env, {"TIMEOUT": "float"})
    assert result.env["TIMEOUT"] == pytest.approx(3.14)
    assert isinstance(result.env["TIMEOUT"], float)


def test_bool_true_variants():
    for raw in ("1", "true", "yes", "on", "True", "YES"):
        r = coerce({"FLAG": raw}, {"FLAG": "bool"})
        assert r.env["FLAG"] is True, f"expected True for {raw!r}"


def test_bool_false_variants():
    for raw in ("0", "false", "no", "off", "False", "NO"):
        r = coerce({"FLAG": raw}, {"FLAG": "bool"})
        assert r.env["FLAG"] is False, f"expected False for {raw!r}"


def test_str_coercion_is_noop(sample_env):
    result = coerce(sample_env, {"NAME": "str"})
    assert result.env["NAME"] == "envoy"
    assert "NAME" in result.coerced_keys


def test_failed_int_coercion_creates_issue(sample_env):
    result = coerce(sample_env, {"RETRIES": "int"})
    assert result.has_issues()
    assert result.issues[0].key == "RETRIES"
    assert result.issues[0].target_type == "int"


def test_failed_coercion_uses_raw_as_fallback(sample_env):
    result = coerce(sample_env, {"RETRIES": "int"})
    assert result.env["RETRIES"] == "bad_int"


def test_failed_coercion_uses_provided_default():
    result = coerce(
        {"RETRIES": "bad_int"},
        {"RETRIES": "int"},
        defaults={"RETRIES": "0"},
    )
    assert result.env["RETRIES"] == "0"


def test_unsupported_type_raises_coerce_error(sample_env):
    with pytest.raises(CoerceError, match="unsupported target type"):
        coerce(sample_env, {"PORT": "list"})


def test_summary_string(sample_env):
    result = coerce(sample_env, {"PORT": "int", "RETRIES": "int"})
    s = result.summary()
    assert "1 key(s) coerced" in s
    assert "1 issue(s)" in s


def test_unrelated_keys_preserved(sample_env):
    result = coerce(sample_env, {"PORT": "int"})
    assert "NAME" in result.env
    assert result.env["NAME"] == "envoy"


def test_invalid_bool_creates_issue():
    result = coerce({"FLAG": "maybe"}, {"FLAG": "bool"})
    assert result.has_issues()
    assert result.issues[0].key == "FLAG"
    issue_str = str(result.issues[0])
    assert "FLAG" in issue_str
    assert "bool" in issue_str
