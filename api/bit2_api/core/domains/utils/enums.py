"""Enums for the application"""
from enum import Enum


class GameTypeEnum(str, Enum):
    """Game Type Enum"""

    DIGITAL_00H = "DIGITAL_00H"
    DIGITAL_21H = "DIGITAL_21H"
    STAR_11H = "STAR_11H"
    STAR_14H = "STAR_14H"
    STAR_18H = "STAR_18H"
    FORTUNE_11H = "FORTUNE_11H"
    FORTUNE_14H = "FORTUNE_14H"
    FORTUNE_18H = "FORTUNE_18H"
