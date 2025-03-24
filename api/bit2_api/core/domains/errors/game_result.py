"""Module for game result errors."""
from bit2_api.core.domains.errors import ICoreException


class InvalidGameResultError(ICoreException):
    """Exception raised when a game result is invalid."""

    message = "The game result is invalid."
    http_code = 400
    key = "invalid_game_result"
