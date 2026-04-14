"""Tests for envoy.patcher."""

import pytest
from envoy.patcher import patch, patch_file, PatchError, PatchResult


SAMPLE = """APP_ENV=production
DB_HOST=localhost
DB_PORT=5432
SECRET_KEY="old-secret"
"""


def test_patch_updates_existing_key():
    new_src, result = patch(SAMPLE, {"DB_HOST": "db.example.com"})
    assert "DB_HOST=db.example.com" in new_src
    assert result.applied == {"DB_HOST": "db.example.com"}
    assert result.added == {}


def test_patch_multiple_keys():
    new_src, result = patch(SAMPLE, {"DB_HOST": "remote", "DB_PORT": "5433"})
    assert "DB_HOST=remote" in new_src
    assert "DB_PORT=5433" in new_src
    assert len(result.applied) == 2


def test_patch_adds_missing_key_by_default():
    new_src, result = patch(SAMPLE, {"NEW_KEY": "hello"})
    assert "NEW_KEY=hello" in new_src
    assert result.added == {"NEW_KEY": "hello"}


def test_patch_does_not_add_when_disabled():
    new_src, result = patch(SAMPLE, {"NEW_KEY": "hello"}, add_missing=False)
    assert "NEW_KEY" not in new_src
    assert result.added == {}


def test_patch_preserves_unrelated_lines():
    new_src, _ = patch(SAMPLE, {"DB_HOST": "other"})
    assert "APP_ENV=production" in new_src
    assert "DB_PORT=5432" in new_src


def test_patch_quotes_value_with_spaces():
    new_src, _ = patch(SAMPLE, {"APP_ENV": "my value"})
    assert 'APP_ENV="my value"' in new_src


def test_patch_quotes_value_with_hash():
    new_src, _ = patch(SAMPLE, {"APP_ENV": "val#ue"})
    assert 'APP_ENV="val#ue"' in new_src


def test_patch_preserve_quotes_double():
    new_src, _ = patch(SAMPLE, {"SECRET_KEY": "new-secret"}, preserve_quotes=True)
    assert 'SECRET_KEY="new-secret"' in new_src


def test_patch_preserve_quotes_single():
    src = "TOKEN='old-token'\n"
    new_src, _ = patch(src, {"TOKEN": "new-token"}, preserve_quotes=True)
    assert "TOKEN='new-token'" in new_src


def test_has_changes_true_when_applied():
    _, result = patch(SAMPLE, {"DB_HOST": "x"})
    assert result.has_changes is True


def test_has_changes_false_when_no_match_and_no_add():
    _, result = patch(SAMPLE, {"GHOST": "x"}, add_missing=False)
    assert result.has_changes is False


def test_summary_reports_updated_and_added():
    _, result = patch(SAMPLE, {"DB_HOST": "x", "BRAND_NEW": "y"})
    s = result.summary()
    assert "updated" in s
    assert "added" in s


def test_summary_no_changes():
    _, result = patch(SAMPLE, {"GHOST": "x"}, add_missing=False)
    assert result.summary() == "No changes applied."


def test_patch_file_writes_changes(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE, encoding="utf-8")
    result = patch_file(env_file, {"DB_PORT": "9999"})
    content = env_file.read_text(encoding="utf-8")
    assert "DB_PORT=9999" in content
    assert result.applied == {"DB_PORT": "9999"}


def test_patch_file_raises_on_missing_file(tmp_path):
    with pytest.raises(PatchError, match="Cannot read"):
        patch_file(tmp_path / "nonexistent.env", {"KEY": "val"})
