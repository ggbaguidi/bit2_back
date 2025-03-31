from sqlalchemy import Column, Date, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY

from .base_model import BaseModel


class GameResult(BaseModel):
    """
    Game Result Model
    """

    __tablename__ = "game_result"
    draw_date = Column(Date, nullable=False)
    numbers = Column(ARRAY(Integer), nullable=False)
    bonus = Column(Integer, nullable=True)
    type = Column(Text, nullable=False)
    __table_args__ = ({"schema": "game"},)
