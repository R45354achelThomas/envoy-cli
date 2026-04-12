"""Unit tests for envoy.diff."""

from envoy.diff import diff_envs, _is_secret, _mask


BASE = {
    "DB_HOST": "localhost",
    "DB_PASSWORD": "old_secret",
    "APP_ENV": "staging",
    "REMOVED_KEY": "gone",
}

TARGET = {
    "DB_HOST": "db.prod.internal",
    "DB_PASSWORD": "new_super_secret",
    "APP_ENV": "staging",
    "ADDED_KEY": "fresh",
}


def test_detects_added_keys():
    result = diff_envs(BASE, TARGET)
    keys = [e.key for e in result.added]
    assert "ADDED_KEY" in keys


def test_detects_removed_keys():
    result = diff_envs(BASE, TARGET)
    keys = [e.key for e in result.removed]
    assert "REMOVED_KEY" in keys


def test_detects_changed_keys():
    result = diff_envs(BASE, TARGET)
    keys = [e.key for e in result.changed]
    assert "DB_HOST" in keys
    assert "DB_PASSWORD" in keys


def test_unchanged_excluded_by_default():
    result = diff_envs(BASE, TARGET)
    assert not result.unchanged


def test_unchanged_included_when_requested():
    result = diff_envs(BASE, TARGET, show_unchanged=True)
    keys = [e.key for e in result.unchanged]
    assert "APP_ENV" in keys


def test_has_changes_true():
    result = diff_envs(BASE, TARGET)
    assert result.has_changes()


def test_has_changes_false():
    result = diff_envs(BASE, BASE)
    assert not result.has_changes()


def test_secret_detection():
    assert _is_secret("DB_PASSWORD")
    assert _is_secret("API_SECRET_KEY")
    assert _is_secret("AUTH_TOKEN")
    assert not _is_secret("DB_HOST")
    assert not _is_secret("APP_ENV")


def test_secret_values_masked_in_display():
    result = diff_envs(BASE, TARGET)
    pwd_entry = next(e for e in result.changed if e.key == "DB_PASSWORD")
    assert pwd_entry.is_secret
    assert pwd_entry.display_old != pwd_entry.old_value
    assert "*" in pwd_entry.display_old
    assert "*" in pwd_entry.display_new


def test_non_secret_values_not_masked():
    result = diff_envs(BASE, TARGET)
    host_entry = next(e for e in result.changed if e.key == "DB_HOST")
    assert not host_entry.is_secret
    assert host_entry.display_new == "db.prod.internal"


def test_mask_short_value():
    assert _mask("ab") == "****"


def test_mask_long_value():
    masked = _mask("abcdefgh")
    assert masked.startswith("ab")
    assert masked.endswith("gh")
    assert "****" in masked
