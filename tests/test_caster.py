import pytest
from envoy.caster import cast, CastResult, CastError, _cast_one


@pytest.fixture
def sample_env():
    return {
        "PORT": "8080",
        "DEBUG": "true",
        "RATIO": "3.14",
        "TAGS": "web,api,v2",
        "NAME": "envoy",
    }


def test_cast_returns_cast_result(sample_env):
    result = cast(sample_env, {})
    assert isinstance(result, CastResult)


def test_no_schema_keeps_strings(sample_env):
    result = cast(sample_env, {})
    assert result.casted["PORT"] == "8080"


def test_int_cast(sample_env):
    result = cast(sample_env, {"PORT": "int"})
    assert result.casted["PORT"] == 8080
    assert isinstance(result.casted["PORT"], int)


def test_float_cast(sample_env):
    result = cast(sample_env, {"RATIO": "float"})
    assert abs(result.casted["RATIO"] - 3.14) < 1e-9


def test_bool_true_variants():
    for val in ("true", "1", "yes", "on", "True", "YES"):
        assert _cast_one(val, "bool") is True


def test_bool_false_variants():
    for val in ("false", "0", "no", "off", "False", "NO"):
        assert _cast_one(val, "bool") is False


def test_bool_cast_via_cast(sample_env):
    result = cast(sample_env, {"DEBUG": "bool"})
    assert result.casted["DEBUG"] is True


def test_list_cast(sample_env):
    result = cast(sample_env, {"TAGS": "list"})
    assert result.casted["TAGS"] == ["web", "api", "v2"]


def test_list_cast_single_item():
    result = cast({"K": "only"}, {"K": "list"})
    assert result.casted["K"] == ["only"]


def test_invalid_int_recorded_as_failure():
    result = cast({"PORT": "abc"}, {"PORT": "int"})
    assert result.has_failures()
    assert "PORT" in result.failed
    assert result.casted["PORT"] == "abc"  # original preserved


def test_invalid_bool_recorded_as_failure():
    result = cast({"FLAG": "maybe"}, {"FLAG": "bool"})
    assert result.has_failures()


def test_unknown_type_raises_cast_error():
    with pytest.raises(CastError):
        _cast_one("val", "datetime")


def test_summary_no_failures(sample_env):
    result = cast(sample_env, {})
    assert "0 failure" in result.summary()


def test_summary_with_failures():
    result = cast({"X": "bad"}, {"X": "int"})
    assert "1 failure" in result.summary()


def test_has_failures_false_when_clean(sample_env):
    result = cast(sample_env, {"PORT": "int"})
    assert not result.has_failures()
