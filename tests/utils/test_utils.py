import pytest
import os
from snow_ipa.utils.utils import (
    csv_to_list,
    env_to_dict,
    keys_to_lower,
    replace_values_in_dict,
)


class TestCsvToList:
    @pytest.mark.parametrize(
        "csv_string, expected",
        [
            ("a,b,c", ["a", "b", "c"]),
            ("  a , b , c  ", ["a", "b", "c"]),
            ("'a','b','c'", ["a", "b", "c"]),
            ('"a","b","c"', ["a", "b", "c"]),
            ("", []),
            (",,", []),
        ],
    )
    def test_csv_to_list(self, csv_string, expected):
        assert csv_to_list(csv_string) == expected


class TestEnvToDict:
    @pytest.fixture()
    def setup_env(self, mocker):
        mocker.patch.dict(
            os.environ, {"TEST_PREFIX_KEY1": "value1", "TEST_PREFIX_KEY2": "value2"}
        )

    def test_env_to_dict(self, setup_env):
        result = env_to_dict(env_prefix="TEST_PREFIX")
        expected = {"KEY1": "value1", "KEY2": "value2"}
        assert result == expected

    @pytest.fixture
    def setup_env_empty(self, mocker):
        mocker.patch.dict(os.environ, {})

    def test_env_to_dict_empty(self, setup_env_empty):
        result = env_to_dict("TEST_PREFIX")
        assert result == {}


class TestKeysToLower:
    @pytest.mark.parametrize(
        "input_dict, expected",
        [
            (
                {"Key1": "value1", "KEY2": "value2"},
                {"key1": "value1", "key2": "value2"},
            ),
            ({}, {}),
            ({"key": "value"}, {"key": "value"}),
        ],
    )
    def test_keys_to_lower(self, input_dict, expected):
        assert keys_to_lower(input_dict) == expected


class TestReplaceValuesInDict:
    @pytest.mark.parametrize(
        "input_dict, replacements, expected",
        [
            (
                {"key1": "value1", "key2": "value2"},
                {"key1": "new_value1"},
                {"key1": "new_value1", "key2": "value2"},
            ),
            (
                {"key1": "value1", "key2": "value2"},
                {"key3": "new_value3"},
                {"key1": "value1", "key2": "value2"},
            ),
            ({}, {"key1": "new_value1"}, {}),
        ],
    )
    def test_replace_values_in_dict(self, input_dict, replacements, expected):
        assert replace_values_in_dict(input_dict, replacements) == expected
