"""Tests for envoy.schema_generator."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy.schema_generator import (
    SchemaGeneratorError,
    generate_schema,
    write_schema,
)


@pytest.fixture()
def simple_env(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "APP_NAME=myapp\n"
        "API_KEY=supersecret\n"
        "DB_PASSWORD=hunter2\n"
        "DEBUG=\n"
        "PORT=8080\n"
    )
    return p


def test_generate_schema_returns_dict(simple_env: Path) -> None:
    schema = generate_schema(simple_env)
    assert isinstance(schema, dict)
    assert "required" in schema
    assert "optional" in schema
    assert "secrets" in schema


def test_keys_with_values_are_required(simple_env: Path) -> None:
    schema = generate_schema(simple_env)
    assert "APP_NAME" in schema["required"]
    assert "PORT" in schema["required"]


def test_empty_value_key_is_optional(simple_env: Path) -> None:
    schema = generate_schema(simple_env)
    assert "DEBUG" in schema["optional"]


def test_secret_keys_detected(simple_env: Path) -> None:
    schema = generate_schema(simple_env)
    assert "API_KEY" in schema["secrets"]
    assert "DB_PASSWORD" in schema["secrets"]


def test_non_secret_key_not_in_secrets(simple_env: Path) -> None:
    schema = generate_schema(simple_env)
    assert "APP_NAME" not in schema["secrets"]
    assert "PORT" not in schema["secrets"]


def test_caller_supplied_required_keys(simple_env: Path) -> None:
    schema = generate_schema(simple_env, required_keys=["APP_NAME", "PORT"])
    assert "APP_NAME" in schema["required"]
    assert "PORT" in schema["required"]
    # DEBUG has empty value but was not listed, so goes to optional
    assert "DEBUG" in schema["optional"]


def test_caller_supplied_optional_keys(simple_env: Path) -> None:
    schema = generate_schema(simple_env, optional_keys=["DEBUG", "PORT"])
    assert "DEBUG" in schema["optional"]
    assert "PORT" in schema["optional"]
    assert "APP_NAME" in schema["required"]


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(SchemaGeneratorError, match="File not found"):
        generate_schema(tmp_path / "nonexistent.env")


def test_write_schema_creates_json_file(simple_env: Path, tmp_path: Path) -> None:
    schema = generate_schema(simple_env)
    out = tmp_path / "schemas" / "schema.json"
    write_schema(schema, out)
    assert out.exists()
    loaded = json.loads(out.read_text())
    assert loaded["required"] == schema["required"]
    assert loaded["optional"] == schema["optional"]
    assert loaded["secrets"] == schema["secrets"]


def test_write_schema_creates_parent_dirs(simple_env: Path, tmp_path: Path) -> None:
    schema = generate_schema(simple_env)
    deep = tmp_path / "a" / "b" / "c" / "schema.json"
    write_schema(schema, deep)
    assert deep.exists()
