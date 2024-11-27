import pytest
from datetime import date, datetime, timedelta
import logging
from snow_ipa.utilities.dates import (
    check_valid_date,
    check_valid_date_list,
    current_year_month,
    prev_month_last_date,
)


class TestCheckValidDate:

    def test_check_valid_date(self):
        assert check_valid_date("2022-12-01") is True
        assert check_valid_date("2022-13-01") is False
        assert check_valid_date("invalid-date") is False

    def test_check_valid_date_warning_logging(self, caplog):
        with caplog.at_level(logging.WARNING):
            assert check_valid_date("2022-13-01") is False
            assert any(record.levelname == "WARNING" for record in caplog.records)


class TestValidDateList:

    def test_check_valid_date_list(self):
        assert check_valid_date_list(["2022-12-01", "2022-11-01"]) is True
        assert check_valid_date_list(["2022-12-01", "2022-13-01"]) is False
        assert check_valid_date_list("2022-12-01") is True
        assert check_valid_date_list("invalid-date") is False


def test_current_year_month(monkeypatch):
    class MockDateTime(datetime):
        @classmethod
        def today(cls):
            return cls(2022, 12, 1)

    monkeypatch.setattr("snow_ipa.utilities.dates.datetime", MockDateTime)
    assert current_year_month() == "2022-12"


def test_prev_month_last_date(monkeypatch):
    class MockDateTime(datetime):
        @classmethod
        def today(cls):
            return cls(2022, 12, 1)

    monkeypatch.setattr("snow_ipa.utilities.dates.datetime", MockDateTime)
    assert prev_month_last_date() == date(2022, 11, 30)
