import pytest
from envoy.scorer import score, ScoreResult, ScoreIssue, ScoreError


@pytest.fixture
def clean_env():
    return {"DATABASE_URL": "postgres://localhost/db", "PORT": "8080", "DEBUG": "false"}


def test_score_returns_score_result(clean_env):
    result = score(clean_env)
    assert isinstance(result, ScoreResult)


def test_clean_env_scores_100(clean_env):
    result = score(clean_env)
    assert result.score == 100


def test_clean_env_has_no_issues(clean_env):
    result = score(clean_env)
    assert not result.has_issues()


def test_empty_secret_value_is_error():
    result = score({"SECRET_KEY": ""})
    assert any(i.severity == "error" and i.key == "SECRET_KEY" for i in result.issues)


def test_weak_placeholder_is_error():
    result = score({"DB_PASSWORD": "changeme"})
    assert any(i.severity == "error" and "weak placeholder" in i.message for i in result.issues)


def test_lowercase_key_is_warning():
    result = score({"my_key": "value"})
    assert any(i.severity == "warning" and i.key == "my_key" for i in result.issues)


def test_unresolved_template_is_warning():
    result = score({"APP_NAME": "hello {{world}}"})
    assert any("template" in i.message for i in result.issues)


def test_score_decreases_per_error():
    result = score({"API_SECRET": "", "TOKEN": ""})
    assert result.score <= 80


def test_score_decreases_per_warning():
    result = score({"lowercase": "value"})
    assert result.score == 95


def test_score_minimum_is_zero():
    env = {f"api_secret_{i}": "changeme" for i in range(20)}
    result = score(env)
    assert result.score == 0


def test_summary_contains_score():
    result = score({"KEY": "val"})
    assert "100" in result.summary()


def test_non_dict_raises_score_error():
    with pytest.raises(ScoreError):
        score(["KEY=val"])


def test_issue_str_format():
    issue = ScoreIssue("MY_KEY", "some problem", "warning")
    assert "WARNING" in str(issue)
    assert "MY_KEY" in str(issue)
