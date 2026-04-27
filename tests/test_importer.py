"""Tests for envoy.importer."""
from __future__ import annotations

import json
import os

import pytest

from envoy.importer import ImportError, ImportResult, from_json, from_shell, from_dotenv_text


# ---------------------------------------------------------------------------
# from_shell
# ---------------------------------------------------------------------------

def test_from_shell_returns_import_result(monkeypatch):
    monkeypatch.setenv("TEST_FOO", "bar")
    result = from_shell(keys=["TEST_FOO"])
    assert isinstance(result, ImportResult)


def test_from_shell_imports_specific_keys(monkeypatch):
    monkeypatch.setenv("ENVOY_HOST", "localhost")
    monkeypatch.setenv("ENVOY_PORT", "5432")
    result = from_shell(keys=["ENVOY_HOST"])
    assert "ENVOY_HOST" in result.env
    assert "ENVOY_PORT" not in result.env


def test_from_shell_prefix_filter(monkeypatch):
    monkeypatch.setenv("APP_NAME", "myapp")
    monkeypatch.setenv("DB_HOST", "localhost")
    result = from_shell(prefix="APP_")
    assert "APP_NAME" in result.env
    assert "DB_HOST" not in result.env


def test_from_shell_strip_prefix(monkeypatch):
    monkeypatch.setenv("APP_NAME", "myapp")
    result = from_shell(prefix="APP_", strip_prefix=True)
    assert "NAME" in result.env
    assert result.env["NAME"] == "myapp"


def test_from_shell_source_is_shell(monkeypatch):
    monkeypatch.setenv("ENVOY_X", "1")
    result = from_shell(keys=["ENVOY_X"])
    assert result.source == "shell"


def test_from_shell_skipped_keys_populated(monkeypatch):
    monkeypatch.setenv("KEEP", "yes")
    monkeypatch.setenv("SKIP", "no")
    result = from_shell(keys=["KEEP"])
    assert "SKIP" in result.skipped_keys


# ---------------------------------------------------------------------------
# from_json
# ---------------------------------------------------------------------------

def test_from_json_basic():
    data = json.dumps({"HOST": "localhost", "PORT": "5432"})
    result = from_json(data)
    assert result.env["HOST"] == "localhost"
    assert result.env["PORT"] == "5432"


def test_from_json_coerces_values_to_str():
    data = json.dumps({"PORT": 5432, "DEBUG": True})
    result = from_json(data)
    assert result.env["PORT"] == "5432"
    assert result.env["DEBUG"] == "True"


def test_from_json_invalid_raises():
    with pytest.raises(ImportError, match="Invalid JSON"):
        from_json("not-json")


def test_from_json_non_object_raises():
    with pytest.raises(ImportError, match="object"):
        from_json("[1, 2, 3]")


def test_from_json_key_filter():
    data = json.dumps({"A": "1", "B": "2", "C": "3"})
    result = from_json(data, keys=["A", "C"])
    assert "A" in result.env
    assert "C" in result.env
    assert "B" not in result.env
    assert "B" in result.skipped_keys


def test_from_json_source_is_json():
    result = from_json(json.dumps({"X": "1"}))
    assert result.source == "json"


# ---------------------------------------------------------------------------
# from_dotenv_text
# ---------------------------------------------------------------------------

def test_from_dotenv_text_basic():
    text = "HOST=localhost\nPORT=5432\n"
    result = from_dotenv_text(text)
    assert result.env["HOST"] == "localhost"
    assert result.env["PORT"] == "5432"


def test_from_dotenv_text_key_filter():
    text = "HOST=localhost\nPORT=5432\n"
    result = from_dotenv_text(text, keys=["HOST"])
    assert "HOST" in result.env
    assert "PORT" not in result.env


def test_from_dotenv_text_source_is_dotenv():
    result = from_dotenv_text("KEY=val")
    assert result.source == "dotenv"


# ---------------------------------------------------------------------------
# ImportResult helpers
# ---------------------------------------------------------------------------

def test_has_skipped_false_when_none():
    r = ImportResult(env={"A": "1"}, source="json", imported_keys=["A"], skipped_keys=[])
    assert not r.has_skipped()


def test_has_skipped_true_when_some():
    r = ImportResult(env={}, source="json", imported_keys=[], skipped_keys=["B"])
    assert r.has_skipped()


def test_summary_includes_count_and_source():
    r = ImportResult(env={"A": "1"}, source="shell", imported_keys=["A"], skipped_keys=[])
    assert "1" in r.summary()
    assert "shell" in r.summary()
