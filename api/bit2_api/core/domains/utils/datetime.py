"""
This module provides utility functions for converting between
datetime objects and strings in a specific format."""
from datetime import date, datetime

from bit2_api.core.domains.errors.common import (
    DateStringFormatError,
    DateTimeStringFormatError,
)

DATETIME_STR_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_STR_FORMAT = "%Y-%m-%d"


def string_to_datetime(datetime_str: str) -> datetime:
    """Converts datetime string to datetime object."""
    try:
        return datetime.strptime(datetime_str, DATETIME_STR_FORMAT)
    except ValueError as error:
        raise DateTimeStringFormatError from error


def datetime_to_string(datetime_obj: datetime) -> str:
    """Converts datetime object to datetime string."""
    return datetime_obj.strftime(DATETIME_STR_FORMAT)


def string_to_date(date_str: str) -> date:
    """Converts date string to date object."""
    try:
        return datetime.strptime(date_str, DATE_STR_FORMAT).date()
    except ValueError as error:
        raise DateStringFormatError from error


def date_to_string(date_obj: date) -> str:
    """Converts date object to date string."""
    return date_obj.strftime(DATE_STR_FORMAT)
