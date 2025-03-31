# pylint: disable=unidiomatic-typecheck
"""
Utils function
"""
import re
from datetime import date, datetime
from functools import partial
from json import dumps
from typing import List
from uuid import UUID

from bit2_api.core.domains.utils.datetime import date_to_string, datetime_to_string


def convert_string_to_snake_case(string: str) -> str:
    """
    Converts a string to snake_case.
    Args:
        string (str): The string to be converted.

    Returns:
        str: The string in snake_case
    """
    all_cap_re = re.compile("([a-z0-9])([A-Z])")
    first_cap_re = re.compile("(.)([A-Z][a-z]+)")
    interm_name = first_cap_re.sub(r"\1_\2", string)
    return all_cap_re.sub(r"\1_\2", interm_name).lower()


def to_json(array, keys_to_ignore: List[str] = None) -> str:
    """Converts an array to JSON with the possibility to ignore some keys."""

    def get_dict_or_value(keys_to_ignore: List[str], obj: object):
        """Converts an array to JSON with the possibility to ignore some keys."""
        if isinstance(obj, date) and type(obj) == date:
            return date_to_string(obj)
        if isinstance(obj, datetime) and type(obj) == datetime:
            return datetime_to_string(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if keys_to_ignore is not None:
            return {x: obj.__dict__[x] for x in obj.__dict__ if x not in keys_to_ignore}
        return obj.__dict__

    get_dict_or_value_partial = partial(get_dict_or_value, keys_to_ignore)
    return dumps(array, default=get_dict_or_value_partial)


def response_to_json(response, keys_to_ignore: List[str] = None) -> str:
    """Converts a response to JSON with the possibility to ignore some keys."""
    response_json = response.json()

    # Recursively delete keys_to_ignore
    def delete_keys_to_ignore(keys_to_ignore, obj):
        if isinstance(obj, dict):
            for key in keys_to_ignore:
                if key in obj:
                    del obj[key]
            for key in obj:
                delete_keys_to_ignore(keys_to_ignore, obj[key])
        elif isinstance(obj, list):
            for item in obj:
                delete_keys_to_ignore(keys_to_ignore, item)
        return obj

    if keys_to_ignore is not None:
        delete_keys_to_ignore(keys_to_ignore, response_json)

    return dumps(response_json)
