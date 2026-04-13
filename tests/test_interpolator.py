"""Tests for envoy.interpolator."""

import pytest

from envoy.interpolator import (
    InterpolationError,
    interpolate_env,
    interpolate_value,
)


# ---------------------------------------------------------------------------
# interpolate_value
# ---------------------------------------------------------------------------

def test_no_references_unchanged():
    assert interpolate_value("hello world", {}) == "hello world"


def test_brace_reference_resolved():
    result = interpolate_value("${HOST}:5432", {"HOST": "localhost"})
    assert result == "localhost:5432"


def test_bare_reference_resolved():
    result = interpolate_value("$USER@example.com", {"USER": "alice"})
    assert result == "alice@example.com"


def test_default_value_used_when_var_missing():
    result = interpolate_value("${PORT:-8080}", {})
    assert result == "8080"


def test_default_value_ignored_when_var_present():
    result = interpolate_value("${PORT:-8080}", {"PORT": "9000"})
    assert result == "9000"


def test_unresolved_left_as_is_by_default():
    result = interpolate_value("${MISSING}", {})
    assert result == "${MISSING}"


def test_strict_mode_raises_on_missing_brace_ref():
    with pytest.raises(InterpolationError) as exc_info:
        interpolate_value("${MISSING}", {}, strict=True)
    assert "MISSING" in str(exc_info.value)


def test_multiple_references_in_one_value():
    env = {"PROTO": "https", "HOST": "example.com", "PORT": "443"}
    result = interpolate_value("${PROTO}://${HOST}:${PORT}", env)
    assert result == "https://example.com:443"


# ---------------------------------------------------------------------------
# interpolate_env
# ---------------------------------------------------------------------------

def test_interpolate_env_basic():
    pairs = {"HOST": "localhost", "DSN": "postgres://${HOST}/db"}
    result = interpolate_env(pairs)
    assert result["DSN"] == "postgres://localhost/db"


def test_interpolate_env_forward_reference_unresolved():
    # LATER is defined after DSN so it is not yet in resolved when DSN is processed
    pairs = {"DSN": "postgres://${LATER}/db", "LATER": "myhost"}
    result = interpolate_env(pairs)
    # LATER not yet resolved when DSN is processed → token left as-is
    assert "${LATER}" in result["DSN"]


def test_interpolate_env_uses_base():
    base = {"EXTERNAL": "from-base"}
    pairs = {"VALUE": "${EXTERNAL}-suffix"}
    result = interpolate_env(pairs, base=base)
    assert result["VALUE"] == "from-base-suffix"


def test_interpolate_env_base_not_in_output():
    base = {"BASE_VAR": "x"}
    pairs = {"A": "${BASE_VAR}"}
    result = interpolate_env(pairs, base=base)
    assert "BASE_VAR" not in result


def test_interpolate_env_strict_raises():
    pairs = {"A": "${UNDEFINED}"}
    with pytest.raises(InterpolationError):
        interpolate_env(pairs, strict=True)


def test_interpolate_env_default_syntax_in_env():
    pairs = {"PORT": "${CUSTOM_PORT:-3000}"}
    result = interpolate_env(pairs)
    assert result["PORT"] == "3000"
