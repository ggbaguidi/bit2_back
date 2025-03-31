from .core_exception import ICoreException


class NotFoundError(ICoreException):
    """Error thrown when object is not found"""

    message = "Not found."
    http_code = 404
    key = "notFound"


class DateTimeStringFormatError(ICoreException):
    """Error thrown when a datetime cannot be initialized from string."""

    message = "Invalid datetime string format : must follow 'YYYY-MM-DD HH:MM'"
    http_code = 422
    key = "datetimeStringFormatError"


class DateStringFormatError(ICoreException):
    """Error thrown when a date cannot be initialized from string."""

    message = "Invalid datetime string format : must follow 'YYYY-MM-DD'"
    http_code = 422
    key = "dateStringFormatError"


class CommandValidationError(ICoreException):
    """Error thrown when a command is invalid."""

    message = "Command validation error."
    http_code = 422
    key = "commandValidationError"
