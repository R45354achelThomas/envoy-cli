"""Tests for envoy.prefixer."""
import pytest
from envoy.prefixer import PrefixError, add_prefix, strip_prefix


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "APP_NAME": "envoy",
        "SECRET_KEY": "abc123",
    }


# --- add_prefix ---

def test_add_prefix_returns_prefix_result(sample_env):
    result = add_prefix(sample_env, "MY_")
    assert result.env is not None
    assert isinstance(result.changed_keys, list)


def test_add_prefix_prepends_to_all_keys(sample_env):
    result = add_prefix(sample_env, "MY_")
    for new_key in result.env:
        assert new_key.startswith("MY_")


def test_add_prefix_values_preserved(sample_env):
    result = add_prefix(sample_env, "MY_")
    assert result.env["MY_DB_HOST"] == "localhost"
    assert result.env["MY_SECRET_KEY"] == "abc123"


def test_add_prefix_all_keys_in_changed(sample_env):
    result = add_prefix(sample_env, "MY_")
    assert len(result.changed_keys) == len(sample_env)
    assert result.has_changes()


def test_add_prefix_skip_existing_leaves_prefixed_key_unchanged():
    env = {"APP_FOO": "1", "BAR": "2"}
    result = add_prefix(env, "APP_", skip_existing=True)
    assert "APP_FOO" in result.env
    assert "APP_BAR" in result.env
    assert "APP_APP_FOO" not in result.env
    assert "APP_FOO" in result.skipped_keys


def test_add_prefix_no_skip_double_prefixes_existing():
    env = {"APP_FOO": "1"}
    result = add_prefix(env, "APP_", skip_existing=False)
    assert "APP_APP_FOO" in result.env
    assert result.skipped_keys == []


def test_add_prefix_empty_prefix_raises():
    with pytest.raises(PrefixError):
        add_prefix({"A": "1"}, "")


def test_add_prefix_summary_contains_count(sample_env):
    result = add_prefix(sample_env, "X_")
    assert "4 key(s) transformed" in result.summary()


# --- strip_prefix ---

def test_strip_prefix_removes_prefix():
    env = {"APP_HOST": "localhost", "APP_PORT": "80"}
    result = strip_prefix(env, "APP_")
    assert "HOST" in result.env
    assert "PORT" in result.env
    assert result.env["HOST"] == "localhost"


def test_strip_prefix_non_matching_skipped_by_default():
    env = {"APP_HOST": "localhost", "OTHER": "value"}
    result = strip_prefix(env, "APP_")
    assert "OTHER" in result.env
    assert "OTHER" in result.skipped_keys


def test_strip_prefix_non_matching_raises_when_skip_disabled():
    env = {"APP_HOST": "localhost", "OTHER": "value"}
    with pytest.raises(PrefixError, match="OTHER"):
        strip_prefix(env, "APP_", skip_non_matching=False)


def test_strip_prefix_empty_prefix_raises():
    with pytest.raises(PrefixError):
        strip_prefix({"A": "1"}, "")


def test_strip_prefix_result_in_empty_key_raises():
    env = {"APP_": "value"}  # stripping 'APP_' leaves empty string
    with pytest.raises(PrefixError, match="empty key"):
        strip_prefix(env, "APP_")


def test_strip_prefix_has_changes_false_when_nothing_stripped():
    env = {"OTHER": "value"}
    result = strip_prefix(env, "APP_", skip_non_matching=True)
    assert not result.has_changes()


def test_strip_prefix_summary_with_skipped():
    env = {"APP_HOST": "h", "UNRELATED": "u"}
    result = strip_prefix(env, "APP_")
    assert "1 key(s) transformed" in result.summary()
    assert "1 key(s) skipped" in result.summary()
