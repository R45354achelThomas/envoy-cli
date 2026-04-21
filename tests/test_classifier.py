"""Tests for envoy.classifier."""

import pytest

from envoy.classifier import ClassifyError, ClassifyResult, classify, _UNCATEGORIZED


@pytest.fixture()
def sample_env() -> dict:
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DATABASE_URL": "postgres://localhost/mydb",
        "JWT_SECRET": "s3cr3t",
        "API_KEY": "key-abc",
        "SMTP_HOST": "mail.example.com",
        "S3_BUCKET": "my-bucket",
        "LOG_LEVEL": "INFO",
        "FEATURE_DARK_MODE": "true",
        "APP_NAME": "myapp",
        "PORT": "8080",
    }


def test_classify_returns_classify_result(sample_env):
    result = classify(sample_env)
    assert isinstance(result, ClassifyResult)


def test_database_keys_grouped(sample_env):
    result = classify(sample_env)
    assert result.has_category("database")
    db = result.categories["database"]
    assert "DB_HOST" in db
    assert "DB_PORT" in db
    assert "DATABASE_URL" in db


def test_auth_keys_grouped(sample_env):
    result = classify(sample_env)
    assert result.has_category("auth")
    auth = result.categories["auth"]
    assert "JWT_SECRET" in auth
    assert "API_KEY" in auth


def test_email_keys_grouped(sample_env):
    result = classify(sample_env)
    assert result.has_category("email")
    assert "SMTP_HOST" in result.categories["email"]


def test_storage_keys_grouped(sample_env):
    result = classify(sample_env)
    assert result.has_category("storage")
    assert "S3_BUCKET" in result.categories["storage"]


def test_logging_keys_grouped(sample_env):
    result = classify(sample_env)
    assert result.has_category("logging")
    assert "LOG_LEVEL" in result.categories["logging"]


def test_feature_keys_grouped(sample_env):
    result = classify(sample_env)
    assert result.has_category("feature")
    assert "FEATURE_DARK_MODE" in result.categories["feature"]


def test_network_key_grouped(sample_env):
    result = classify(sample_env)
    assert result.has_category("network")
    assert "PORT" in result.categories["network"]


def test_uncategorized_key(sample_env):
    result = classify(sample_env)
    assert "APP_NAME" in result.uncategorized()


def test_category_for_returns_correct_category(sample_env):
    result = classify(sample_env)
    assert result.category_for("DB_HOST") == "database"
    assert result.category_for("JWT_SECRET") == "auth"
    assert result.category_for("APP_NAME") == _UNCATEGORIZED


def test_summary_lists_all_categories(sample_env):
    result = classify(sample_env)
    summary = result.summary()
    assert "database" in summary
    assert "auth" in summary


def test_custom_patterns_take_precedence():
    env = {"MYAPP_TOKEN": "abc", "MYAPP_HOST": "localhost"}
    result = classify(env, custom_patterns={"internal": ["MYAPP_"]})
    assert "MYAPP_TOKEN" in result.categories.get("internal", {})
    assert "MYAPP_HOST" in result.categories.get("internal", {})


def test_empty_env_returns_empty_result():
    result = classify({})
    assert result.categories == {}
    assert result.key_map == {}
    assert result.summary() == "no keys"


def test_non_dict_raises_classify_error():
    with pytest.raises(ClassifyError):
        classify(["KEY=VALUE"])  # type: ignore[arg-type]
