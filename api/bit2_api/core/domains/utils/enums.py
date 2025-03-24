"""Enums for the application"""
from enum import Enum


class GameTypeEnum(str, Enum):
    """Game Type Enum"""

    STAR = "STAR"
    FORTUNE = "FORTUNE"
    DIGITAL = "DIGITAL"
