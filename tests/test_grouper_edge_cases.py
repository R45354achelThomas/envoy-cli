"""Edge-case tests for envoy.grouper."""
import pytest

from envoy.grouper import group, GroupResult


def test_empty_env_returns_empty_result():
    result = group({})
    assert result.groups == {}
    assert result.ungrouped == {}
    assert result.summary() == "no keys"


def test_all_keys_ungrouped_when_no_separator_match():
    env = {"NOPREFIX": "val", "ALSONOPREFIX": "x"}
    result = group(env, separator="_")
    # keys without underscore have no second segment -> ungrouped
    assert not result.groups
    assert set(result.ungrouped.keys()) == {"NOPREFIX", "ALSONOPREFIX"}


def test_values_preserved_in_groups():
    env = {"DB_HOST": "myhost", "DB_PORT": "9999"}
    result = group(env)
    assert result.groups["DB"]["DB_HOST"] == "myhost"
    assert result.groups["DB"]["DB_PORT"] == "9999"


def test_min_prefix_length_zero_groups_everything():
    env = {"A_X": "1", "B_Y": "2"}
    result = group(env, min_prefix_length=0)
    assert "A" in result.groups
    assert "B" in result.groups
    assert not result.ungrouped


def test_prefix_map_case_insensitive_matching():
    env = {"db_host": "h", "DB_PORT": "5432"}
    result = group(env, prefix_map={"DB": "database"})
    assert "database" in result.groups
    assert set(result.groups["database"].keys()) == {"db_host", "DB_PORT"}


def test_summary_includes_ungrouped_count():
    env = {"DB_HOST": "h", "PORT": "80"}
    result = group(env)
    summary = result.summary()
    assert "ungrouped" in summary


def test_group_names_returns_sorted_list():
    env = {"ZEBRA_A": "1", "ALPHA_B": "2", "MANGO_C": "3"}
    result = group(env)
    names = result.group_names()
    assert names == ["ALPHA", "MANGO", "ZEBRA"]


def test_single_key_with_prefix():
    env = {"AWS_REGION": "us-east-1"}
    result = group(env)
    assert "AWS" in result.groups
    assert result.groups["AWS"]["AWS_REGION"] == "us-east-1"


def test_multiple_underscores_only_first_split():
    env = {"AWS_S3_BUCKET": "my-bucket"}
    result = group(env)
    # should group under AWS, not AWS_S3
    assert "AWS" in result.groups
    assert "AWS_S3" not in result.groups
