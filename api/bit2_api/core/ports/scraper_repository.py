"""This module defines the interface for a scraper."""
from abc import ABC, abstractmethod
from typing import List

from bit2_api.core.domains.models import GameResult


class IScraperRepository(ABC):
    """Interface for a scraper."""

    @abstractmethod
    # def fetch_results(self, week: str) -> List[GameResult]:
    def fetch_results(
        self, month: str, draw: str = "", wait_time: int = 1
    ) -> List[GameResult]:
        """Fetch and parse game results from the source."""
        raise NotImplementedError

    # @abstractmethod
    # def fetch_result(self, draw_date: datetime) -> GameResult:
    #     """Fetch and parse a game result from the source."""
    #     raise NotImplementedError
