"""Tests for the GameResult model."""
from datetime import datetime

from bit2_api.core.domains.models.game_result import GameResult
from bit2_api.core.domains.utils import GameTypeEnum


def test_game_result_initialization():
    """Test the initialization of a GameResult object."""
    draw_date = datetime(2023, 10, 1)
    numbers = [1, 2, 3, 4, 5]
    bonus = 7
    game_type = GameTypeEnum.DIGITAL

    game_result = GameResult(
        draw_date=draw_date, numbers=numbers, bonus=bonus, type=game_type
    )

    assert game_result.draw_date == draw_date
    assert game_result.numbers == numbers
    assert game_result.bonus == bonus
    assert game_result.type == game_type


def test_game_result_optional_bonus():
    """Test the initialization of a GameResult object with an optional bonus."""
    draw_date = datetime(2023, 10, 1)
    numbers = [1, 2, 3, 4, 5]
    game_type = GameTypeEnum.FORTUNE

    game_result = GameResult(
        draw_date=draw_date, numbers=numbers, bonus=None, type=game_type
    )

    assert game_result.draw_date == draw_date
    assert game_result.numbers == numbers
    assert game_result.bonus is None
    assert game_result.type == game_type
