"""Enums for the application"""
from enum import Enum


class GameTypeEnum(str, Enum):
    """Game Type Enum"""

    STAR = "STAR"
    FORTUNE = "FORTUNE"
    DIGITAL = "DIGITAL"
    DIGITAL_1 = "DIGITAL_1"
    DIGITAL_2 = "DIGITAL_2"
    RESULTAT_1 = "RESULTAT_1"
    RESULTAT_2 = "RESULTAT_2"
    RESULTAT_3 = "RESULTAT_3"
