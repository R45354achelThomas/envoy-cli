"""Tests for envoy.exporter module."""

import json
import pytest
from envoy.exporter import export_env, to_shell, to_json, to_yaml, to_dotenv, ExportError


SAMPLE = {
    "APP_NAME": "myapp",
    "DB_PASSWORD": 'p@ss"word',
    "DEBUG": "true",
    "EMPTY_VAR": "",
    "PORT": "8080",
}


def test_shell_export_format():
    result = to_shell({"FOO": "bar", "BAZ": "qux"})
    assert 'export BAZ="qux"' in result
    assert 'export FOO="bar"' in result


def test_shell_export_escapes_double_quotes():
    result = to_shell({"KEY": 'say "hello"'})
    assert 'export KEY="say \\"hello\\""' in result


def test_json_export_is_valid_json():
    result = to_json({"A": "1", "B": "2"})
    parsed = json.loads(result)
    assert parsed == {"A": "1", "B": "2"}


def test_json_export_sorted_keys():
    result = to_json({"Z": "last", "A": "first"})
    parsed = json.loads(result)
    assert list(parsed.keys()) == ["A", "Z"]


def test_yaml_export_simple_values():
    result = to_yaml({"HOST": "localhost", "PORT": "5432"})
    assert "HOST: localhost" in result
    assert "PORT: 5432" in result


def test_yaml_export_quotes_special_chars():
    result = to_yaml({"URL": "http://example.com:8080"})
    assert 'URL: "http://example.com:8080"' in result


def test_yaml_export_empty_value():
    result = to_yaml({"EMPTY": ""})
    assert 'EMPTY: ""' in result


def test_dotenv_export_plain_values():
    result = to_dotenv({"KEY": "simple"})
    assert "KEY=simple" in result


def test_dotenv_export_quotes_values_with_spaces():
    result = to_dotenv({"KEY": "hello world"})
    assert 'KEY="hello world"' in result


def test_dotenv_export_quotes_empty_values():
    result = to_dotenv({"KEY": ""})
    assert 'KEY=""' in result


def test_export_env_dispatches_correctly():
    env = {"X": "1"}
    assert export_env(env, "json") == to_json(env)
    assert export_env(env, "shell") == to_shell(env)
    assert export_env(env, "yaml") == to_yaml(env)
    assert export_env(env, "dotenv") == to_dotenv(env)


def test_export_env_raises_on_unknown_format():
    with pytest.raises(ExportError, match="Unknown export format"):
        export_env({"K": "v"}, "xml")  # type: ignore
