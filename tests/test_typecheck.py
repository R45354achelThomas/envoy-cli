"""Tests for envoy.typecheck."""
import pytest
from envoy.typecheck import typecheck, TypeCheckError, TypeCheckResult, TypeIssue


@pytest.fixture
def sample_env():
    return {
        "PORT": "8080",
        "DEBUG": "true",
        "RATE": "3.14",
        "NAME": "myapp",
        "EMPTY": "",
    }


def test_typecheck_returns_result(sample_env):
    result = typecheck(sample_env, {})
    assert isinstance(result, TypeCheckResult)


def test_no_schema_all_strings(sample_env):
    result = typecheck(sample_env, {})
    assert not result.has_issues()
    assert result.env["PORT"] == "8080"


def test_int_cast_success(sample_env):
    result = typecheck(sample_env, {"PORT": "int"})
    assert not result.has_issues()
    assert result.env["PORT"] == 8080
    assert isinstance(result.env["PORT"], int)


def test_float_cast_success(sample_env):
    result = typecheck(sample_env, {"RATE": "float"})
    assert not result.has_issues()
    assert result.env["RATE"] == pytest.approx(3.14)


def test_bool_true_variants():
    for val in ("true", "True", "TRUE", "1", "yes", "on"):
        result = typecheck({"FLAG": val}, {"FLAG": "bool"})
        assert not result.has_issues(), f"Expected no issues for {val!r}"
        assert result.env["FLAG"] is True


def test_bool_false_variants():
    for val in ("false", "False", "FALSE", "0", "no", "off"):
        result = typecheck({"FLAG": val}, {"FLAG": "bool"})
        assert not result.has_issues()
        assert result.env["FLAG"] is False


def test_int_cast_failure_records_issue():
    result = typecheck({"PORT": "not_a_number"}, {"PORT": "int"})
    assert result.has_issues()
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.key == "PORT"
    assert issue.expected == "int"
    assert issue.actual_value == "not_a_number"


def test_bool_cast_failure_records_issue():
    result = typecheck({"DEBUG": "maybe"}, {"DEBUG": "bool"})
    assert result.has_issues()
    assert result.issues[0].key == "DEBUG"


def test_failed_key_keeps_original_value():
    result = typecheck({"PORT": "abc"}, {"PORT": "int"})
    assert result.env["PORT"] == "abc"


def test_str_type_always_passes(sample_env):
    schema = {k: "str" for k in sample_env}
    result = typecheck(sample_env, schema)
    assert not result.has_issues()


def test_unsupported_type_raises():
    with pytest.raises(TypeCheckError, match="Unsupported type"):
        typecheck({"KEY": "val"}, {"KEY": "list"})


def test_summary_no_issues(sample_env):
    result = typecheck(sample_env, {})
    assert "All values" in result.summary()


def test_summary_with_issues():
    result = typecheck({"PORT": "bad"}, {"PORT": "int"})
    assert "1 type mismatch" in result.summary()


def test_issue_str_representation():
    issue = TypeIssue(key="PORT", expected="int", actual_value="bad", message="cannot convert to int")
    text = str(issue)
    assert "PORT" in text
    assert "int" in text
    assert "bad" in text


def test_keys_not_in_schema_default_to_str(sample_env):
    result = typecheck(sample_env, {"PORT": "int"})
    # NAME is not in schema — should remain a string without issue
    assert result.env["NAME"] == "myapp"
    assert not any(i.key == "NAME" for i in result.issues)
