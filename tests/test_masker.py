"""Tests for envoy.masker."""

import pytest

from envoy.masker import MaskError, MaskResult, mask, DEFAULT_PLACEHOLDER


@pytest.fixture
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PASSWORD": "s3cr3t",
        "API_KEY": "abc123",
        "APP_NAME": "myapp",
        "AUTH_TOKEN": "tok_xyz",
    }


def test_mask_returns_mask_result(sample_env):
    result = mask(sample_env)
    assert isinstance(result, MaskResult)


def test_non_secret_keys_unchanged(sample_env):
    result = mask(sample_env)
    assert result.masked["DB_HOST"] == "localhost"
    assert result.masked["APP_NAME"] == "myapp"


def test_secret_keys_replaced_with_default_placeholder(sample_env):
    result = mask(sample_env)
    assert result.masked["DB_PASSWORD"] == DEFAULT_PLACEHOLDER
    assert result.masked["API_KEY"] == DEFAULT_PLACEHOLDER
    assert result.masked["AUTH_TOKEN"] == DEFAULT_PLACEHOLDER


def test_masked_keys_listed(sample_env):
    result = mask(sample_env)
    assert "DB_PASSWORD" in result.masked_keys
    assert "API_KEY" in result.masked_keys
    assert "AUTH_TOKEN" in result.masked_keys


def test_non_secret_keys_not_in_masked_keys(sample_env):
    result = mask(sample_env)
    assert "DB_HOST" not in result.masked_keys
    assert "APP_NAME" not in result.masked_keys


def test_has_masked_true_when_secrets_present(sample_env):
    result = mask(sample_env)
    assert result.has_masked() is True


def test_has_masked_false_when_no_secrets():
    result = mask({"APP_NAME": "myapp", "PORT": "8080"})
    assert result.has_masked() is False


def test_custom_placeholder(sample_env):
    result = mask(sample_env, placeholder="<REDACTED>")
    assert result.masked["DB_PASSWORD"] == "<REDACTED>"
    assert result.placeholder == "<REDACTED>"


def test_explicit_keys_always_masked(sample_env):
    result = mask(sample_env, keys=["DB_HOST"])
    assert result.masked["DB_HOST"] == DEFAULT_PLACEHOLDER
    assert "DB_HOST" in result.masked_keys


def test_auto_detect_false_skips_pattern_matching():
    env = {"DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}
    result = mask(env, auto_detect=False)
    assert result.masked["DB_PASSWORD"] == "s3cr3t"
    assert result.has_masked() is False


def test_auto_detect_false_still_applies_explicit_keys():
    env = {"DB_PASSWORD": "s3cr3t", "APP_NAME": "myapp"}
    result = mask(env, keys=["DB_PASSWORD"], auto_detect=False)
    assert result.masked["DB_PASSWORD"] == DEFAULT_PLACEHOLDER


def test_empty_placeholder_raises():
    with pytest.raises(MaskError):
        mask({"KEY": "val"}, placeholder="")


def test_summary_string(sample_env):
    result = mask(sample_env)
    s = result.summary()
    assert "masked" in s
    assert str(len(result.masked_keys)) in s


def test_original_env_not_mutated(sample_env):
    original_password = sample_env["DB_PASSWORD"]
    mask(sample_env)
    assert sample_env["DB_PASSWORD"] == original_password
