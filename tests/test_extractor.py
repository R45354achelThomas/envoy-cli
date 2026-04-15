"""Tests for envoy.extractor."""

import pytest

from envoy.extractor import ExtractError, ExtractResult, extract


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "API_KEY": "secret",
        "APP_ENV": "production",
    }


def test_extract_returns_extract_result(sample_env):
    result = extract(sample_env, ["DB_HOST"])
    assert isinstance(result, ExtractResult)


def test_extract_single_key(sample_env):
    result = extract(sample_env, ["DB_HOST"])
    assert result.extracted == {"DB_HOST": "localhost"}


def test_extract_multiple_keys(sample_env):
    result = extract(sample_env, ["DB_HOST", "DB_PORT"])
    assert result.extracted == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_extract_preserves_values(sample_env):
    result = extract(sample_env, ["API_KEY"])
    assert result.extracted["API_KEY"] == "secret"


def test_missing_key_raises_by_default(sample_env):
    with pytest.raises(ExtractError, match="MISSING_KEY"):
        extract(sample_env, ["MISSING_KEY"])


def test_allow_missing_does_not_raise(sample_env):
    result = extract(sample_env, ["MISSING_KEY"], allow_missing=True)
    assert "MISSING_KEY" not in result.extracted
    assert "MISSING_KEY" in result.missing


def test_allow_missing_skips_absent_key(sample_env):
    result = extract(sample_env, ["MISSING_KEY"], allow_missing=True)
    assert "MISSING_KEY" in result.skipped


def test_default_value_used_for_absent_key(sample_env):
    result = extract(sample_env, ["MISSING_KEY"], default="")
    assert result.extracted["MISSING_KEY"] == ""


def test_default_implies_allow_missing(sample_env):
    result = extract(sample_env, ["MISSING_KEY"], default="fallback")
    assert "MISSING_KEY" in result.missing
    assert result.extracted["MISSING_KEY"] == "fallback"


def test_has_missing_false_when_all_found(sample_env):
    result = extract(sample_env, ["DB_HOST", "DB_PORT"])
    assert result.has_missing() is False


def test_has_missing_true_when_absent(sample_env):
    result = extract(sample_env, ["NOPE"], allow_missing=True)
    assert result.has_missing() is True


def test_summary_shows_extracted_count(sample_env):
    result = extract(sample_env, ["DB_HOST", "DB_PORT"])
    assert "extracted=2" in result.summary()


def test_summary_shows_missing_count(sample_env):
    result = extract(sample_env, ["DB_HOST", "NOPE"], allow_missing=True)
    assert "missing=1" in result.summary()


def test_empty_key_list_returns_empty_extracted(sample_env):
    result = extract(sample_env, [])
    assert result.extracted == {}
    assert result.has_missing() is False
