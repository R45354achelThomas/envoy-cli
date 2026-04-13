"""Tests for envoy.linter."""
import pytest
from envoy.linter import lint, LintIssue, LintResult


def test_clean_file_has_no_issues():
    src = "DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=abc123\n"
    result = lint(src)
    assert not result.has_issues
    assert result.summary() == "No lint issues found."


def test_lowercase_key_triggers_L001():
    result = lint("db_host=localhost\n")
    codes = [i.code for i in result.issues]
    assert "L001" in codes


def test_mixed_case_key_triggers_L001():
    result = lint("DbHost=localhost\n")
    assert any(i.code == "L001" for i in result.issues)


def test_duplicate_key_triggers_L003():
    src = "DB_HOST=localhost\nDB_HOST=remotehost\n"
    result = lint(src)
    assert any(i.code == "L003" for i in result.issues)
    assert result.has_errors


def test_duplicate_key_issue_has_correct_first_line():
    src = "DB_HOST=localhost\nDB_HOST=remotehost\n"
    result = lint(src)
    issue = next(i for i in result.issues if i.code == "L003")
    assert "line 1" in issue.message


def test_unquoted_value_with_spaces_triggers_L004():
    result = lint("GREETING=hello world\n")
    assert any(i.code == "L004" for i in result.issues)


def test_quoted_value_with_spaces_no_L004():
    result = lint('GREETING="hello world"\n')
    assert not any(i.code == "L004" for i in result.issues)


def test_blank_lines_and_comments_ignored():
    src = "# This is a comment\n\nDB_HOST=localhost\n"
    result = lint(src)
    assert not result.has_issues


def test_summary_reports_counts():
    src = "db_host=localhost\nDB_HOST=a\nDB_HOST=b\n"
    result = lint(src)
    summary = result.summary()
    assert "error" in summary
    assert "warning" in summary


def test_lint_issue_str_format():
    issue = LintIssue(line=3, key="foo", code="L001", message="Key 'foo' should be uppercase.", severity="warning")
    s = str(issue)
    assert "WARNING" in s
    assert "line 3" in s
    assert "L001" in s


def test_has_errors_false_when_only_warnings():
    result = lint("db_host=localhost\n")
    assert result.has_issues
    assert not result.has_errors


def test_lines_without_equals_are_skipped():
    src = "JUST_A_WORD\nDB_HOST=localhost\n"
    result = lint(src)
    assert not result.has_issues
