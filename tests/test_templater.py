"""Tests for envoy.templater."""
from pathlib import Path

import pytest

from envoy.templater import TemplateError, render, render_file


def test_simple_substitution():
    result = render("HOST={{ HOST }}", {"HOST": "localhost"})
    assert result == "HOST=localhost"


def test_multiple_placeholders():
    tmpl = "DB_HOST={{ DB_HOST }}\nDB_PORT={{ DB_PORT }}"
    env = {"DB_HOST": "127.0.0.1", "DB_PORT": "5432"}
    assert render(tmpl, env) == "DB_HOST=127.0.0.1\nDB_PORT=5432"


def test_default_value_used_when_missing():
    result = render("TIMEOUT={{ TIMEOUT:-30 }}", {})
    assert result == "TIMEOUT=30"


def test_default_value_ignored_when_present():
    result = render("TIMEOUT={{ TIMEOUT:-30 }}", {"TIMEOUT": "60"})
    assert result == "TIMEOUT=60"


def test_empty_default_value():
    result = render("OPTIONAL={{ OPTIONAL:- }}", {})
    assert result == "OPTIONAL="


def test_strict_mode_raises_on_missing_key():
    with pytest.raises(TemplateError) as exc_info:
        render("X={{ MISSING }}", {}, strict=True)
    assert "MISSING" in str(exc_info.value)
    assert exc_info.value.key == "MISSING"


def test_strict_mode_reports_all_missing_keys():
    with pytest.raises(TemplateError) as exc_info:
        render("A={{ A }}\nB={{ B }}", {}, strict=True)
    msg = str(exc_info.value)
    assert "A" in msg
    assert "B" in msg


def test_non_strict_leaves_placeholder():
    result = render("X={{ MISSING }}", {}, strict=False)
    assert "{{ MISSING }}" in result


def test_whitespace_around_key_is_tolerated():
    result = render("V={{  MY_VAR  }}", {"MY_VAR": "hello"})
    assert result == "V=hello"


def test_no_placeholders_returns_template_unchanged():
    tmpl = "# plain comment\nFOO=bar"
    assert render(tmpl, {}) == tmpl


def test_render_file_reads_and_renders(tmp_path: Path):
    tmpl_file = tmp_path / "sample.env.template"
    tmpl_file.write_text("APP={{ APP_NAME }}\nENV={{ APP_ENV:-development }}", encoding="utf-8")
    result = render_file(tmpl_file, {"APP_NAME": "envoy"})
    assert result == "APP=envoy\nENV=development"


def test_render_file_missing_path_raises(tmp_path: Path):
    with pytest.raises(TemplateError):
        render_file(tmp_path / "nonexistent.template", {})
