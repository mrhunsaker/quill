from datetime import date, datetime

import pytest

from quill.core.datetime_insert import (
    DEFAULT_DATETIME_FORMAT,
    calculate_date,
    format_datetime,
    nth_weekday_of_month,
    parse_weekday,
)

_MOMENT = datetime(2024, 11, 28, 9, 5, 0)


def test_format_datetime_default() -> None:
    assert format_datetime(_MOMENT, DEFAULT_DATETIME_FORMAT) == "2024-11-28 09:05"


def test_format_datetime_custom_strftime() -> None:
    assert format_datetime(_MOMENT, "%d/%m/%Y") == "28/11/2024"


def test_format_datetime_custom_dotnet_tokens() -> None:
    assert format_datetime(_MOMENT, "yyyy-MM-dd HH:mm:ss") == "2024-11-28 09:05:00"


def test_nth_weekday_fourth_thursday_november() -> None:
    # US Thanksgiving 2024 = 4th Thursday of November.
    assert nth_weekday_of_month(2024, 11, 4, parse_weekday("Thursday")) == date(2024, 11, 28)


def test_nth_weekday_last() -> None:
    assert nth_weekday_of_month(2024, 11, -1, parse_weekday("Friday")) == date(2024, 11, 29)


def test_calculate_date_fixed_day() -> None:
    assert calculate_date(2024, 7, day=4) == date(2024, 7, 4)


def test_calculate_date_requires_rule() -> None:
    with pytest.raises(ValueError):
        calculate_date(2024, 7)


def test_parse_weekday_abbreviation() -> None:
    assert parse_weekday("thu") == 3
    with pytest.raises(ValueError):
        parse_weekday("funday")
