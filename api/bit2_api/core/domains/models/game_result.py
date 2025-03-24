"""This module contains the GameResult class, which represents a game result."""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from bit2_api.core.domains.utils import GameTypeEnum


@dataclass
class GameResult:
    """Represents a game result."""

    draw_date: datetime
    numbers: List[int]
    bonus: Optional[int]
    type: GameTypeEnum
