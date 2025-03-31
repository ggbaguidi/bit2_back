"""
This module defines the interface for a game result repository.
It provides methods for saving, retrieving, and deleting game results.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

from bit2_api.core.domains.commands import ExtractGameResultCommand
from bit2_api.core.domains.models import GameResult
from bit2_api.core.domains.utils.enums import GameTypeEnum
from bit2_api.core.ports.session import ISession


class IGameResultRepository(ABC):
    """Interface for a game result repository."""

    @abstractmethod
    def get_by_draw_date(
        self,
        draw_date: datetime,
        db_session: ISession,
    ) -> GameResult:
        """Method to get a game result by its draw date"""
        raise NotImplementedError

    @abstractmethod
    def get_by_type(
        self,
        game_type: GameTypeEnum,
        db_session: ISession,
    ) -> List[GameResult]:
        """Method to get game results by game type"""
        raise NotImplementedError

    @abstractmethod
    def get_all(
        self,
        db_session: ISession,
    ) -> List[GameResult]:
        """Method to get all game results"""
        raise NotImplementedError

    @abstractmethod
    def create(
        self, command: ExtractGameResultCommand, db_session: ISession
    ) -> GameResult:
        """Creates a game result"""
        raise NotImplementedError

    @abstractmethod
    def delete(
        self, draw_date: datetime, game_type: GameTypeEnum, db_session: ISession
    ) -> None:
        """Method to delete a game result"""
        raise NotImplementedError
