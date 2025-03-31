from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from bit2_api.core.domains.utils import GameTypeEnum


@dataclass
class ExtractGameResultCommand:
    """
    Represents a game result ccommand.
    """

    draw_date: datetime
    numbers: List[int]
    bonus: Optional[int]
    type: GameTypeEnum
