"""Tests for envoy.profiler."""

import json
import pytest
from pathlib import Path

from envoy.profiler import (
    ProfileError,
    ProfileEntry,
    ProfileResult,
    load_profile,
    check_profile,
)


@pytest.fixture
def profile_file(tmp_path: Path) -> Path:
    data = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": None}
    p = tmp_path / "profile.json"
    p.write_text(json.dumps(data))
    return p


def test_load_profile_returns_dict(profile_file):
    profile = load_profile(profile_file)
    assert isinstance(profile, dict)
    assert profile["DB_HOST"] == "localhost"
    assert profile["SECRET_KEY"] is None


def test_load_profile_missing_file_raises(tmp_path):
    with pytest.raises(ProfileError, match="not found"):
        load_profile(tmp_path / "nonexistent.json")


def test_load_profile_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not json{{")
    with pytest.raises(ProfileError, match="Invalid JSON"):
        load_profile(bad)


def test_load_profile_non_object_raises(tmp_path):
    arr = tmp_path / "arr.json"
    arr.write_text(json.dumps(["a", "b"]))
    with pytest.raises(ProfileError, match="JSON object"):
        load_profile(arr)


def test_compliant_env_passes():
    env = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": "abc123"}
    profile = {"DB_HOST": "localhost", "DB_PORT": "5432", "SECRET_KEY": None}
    result = check_profile(env, profile, "production")
    assert result.is_compliant
    assert result.mismatches == []


def test_wrong_value_is_mismatch():
    env = {"DB_HOST": "remotehost", "DB_PORT": "5432"}
    profile = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    result = check_profile(env, profile, "staging")
    assert not result.is_compliant
    assert len(result.mismatches) == 1
    assert result.mismatches[0].key == "DB_HOST"


def test_missing_required_key_is_mismatch():
    env = {"DB_PORT": "5432"}
    profile = {"DB_HOST": "localhost", "DB_PORT": "5432"}
    result = check_profile(env, profile, "test")
    assert not result.is_compliant
    missing = [e for e in result.mismatches if e.key == "DB_HOST"]
    assert len(missing) == 1
    assert missing[0].actual is None


def test_none_profile_value_requires_presence():
    env_missing = {"DB_PORT": "5432"}
    profile = {"SECRET_KEY": None}
    result = check_profile(env_missing, profile, "check")
    assert not result.is_compliant

    env_present = {"SECRET_KEY": "anything"}
    result2 = check_profile(env_present, profile, "check")
    assert result2.is_compliant


def test_summary_compliant():
    result = ProfileResult(profile_name="prod", entries=[])
    assert "COMPLIANT" in result.summary()
    assert "prod" in result.summary()


def test_summary_non_compliant():
    entry = ProfileEntry(key="X", expected="a", actual="b")
    result = ProfileResult(profile_name="dev", entries=[entry])
    assert "NON-COMPLIANT" in result.summary()


def test_entry_to_dict():
    entry = ProfileEntry(key="FOO", expected="bar", actual="bar")
    d = entry.to_dict()
    assert d["key"] == "FOO"
    assert d["matches"] is True
