"""Tests for envoy.sorter."""

import pytest

from envoy.sorter import SortError, SortResult, sort


@pytest.fixture()
def sample_env():
    return {"ZEBRA": "1", "APPLE": "2", "MANGO": "3", "banana": "4"}


def test_sort_returns_sort_result(sample_env):
    result = sort(sample_env)
    assert isinstance(result, SortResult)


def test_keys_sorted_alphabetically_case_insensitive(sample_env):
    result = sort(sample_env)
    assert list(result.sorted_env.keys()) == ["APPLE", "banana", "MANGO", "ZEBRA"]


def test_keys_sorted_case_sensitive(sample_env):
    result = sort(sample_env, case_sensitive=True)
    # uppercase letters sort before lowercase in ASCII
    assert list(result.sorted_env.keys()) == ["APPLE", "MANGO", "ZEBRA", "banana"]


def test_has_changes_true_when_order_differs(sample_env):
    result = sort(sample_env)
    assert result.has_changes is True


def test_has_changes_false_when_already_sorted():
    already = {"ALPHA": "1", "BETA": "2", "GAMMA": "3"}
    result = sort(already)
    assert result.has_changes is False


def test_summary_no_changes():
    already = {"A": "1", "B": "2"}
    result = sort(already)
    assert "no changes" in result.summary().lower()


def test_summary_with_changes(sample_env):
    result = sort(sample_env)
    assert "4" in result.summary()


def test_group_ordering_respected():
    env = {"DB_HOST": "h", "APP_NAME": "n", "DB_PASS": "p", "APP_PORT": "8080"}
    groups = [["APP_NAME", "APP_PORT"], ["DB_HOST", "DB_PASS"]]
    result = sort(env, groups=groups)
    keys = list(result.sorted_env.keys())
    assert keys.index("APP_NAME") < keys.index("DB_HOST")
    assert keys.index("APP_PORT") < keys.index("DB_HOST")


def test_ungrouped_keys_appended_at_end():
    env = {"ZEBRA": "z", "APP_NAME": "n", "EXTRA": "e"}
    groups = [["APP_NAME"]]
    result = sort(env, groups=groups)
    keys = list(result.sorted_env.keys())
    assert keys[0] == "APP_NAME"
    assert set(keys[1:]) == {"EXTRA", "ZEBRA"}


def test_group_keys_not_in_env_ignored():
    env = {"ALPHA": "1", "BETA": "2"}
    groups = [["ALPHA", "MISSING_KEY"]]
    result = sort(env, groups=groups)
    assert "MISSING_KEY" not in result.sorted_env


def test_to_dotenv_output(sample_env):
    result = sort(sample_env)
    output = result.to_dotenv()
    for key in result.sorted_env:
        assert key in output


def test_to_dotenv_quotes_values_with_spaces():
    env = {"MSG": "hello world"}
    result = sort(env)
    assert '"hello world"' in result.to_dotenv()


def test_sort_raises_on_non_dict():
    with pytest.raises(SortError):
        sort(["not", "a", "dict"])  # type: ignore
