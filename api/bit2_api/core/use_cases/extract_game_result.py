"""Use case for extracting game results."""
import logging
from dataclasses import replace

from bit2_api.core.domains.commands import ExtractGameResultCommand
from bit2_api.core.domains.models import GameResult
from bit2_api.core.ports import (
    IDatabaseClientRepository,
    IGameResultRepository,
    IScraperRepository,
)

logger = logging.getLogger(__name__)


class ExtractGameResult:
    """
    Use case for extracting game results.
    """

    def __init__(
        self,
        game_repository: IGameResultRepository,
        database_client: IDatabaseClientRepository = None,
    ):
        """
        Initialize the ExtractGameResult use case.
        :param scraper_repository: The scraper repository to fetch game results.
        :param database_client: The database client to store game results.
        """
        self.game_repository = game_repository
        self.session = (
            database_client.get_db_session() if database_client is not None else None
        )

    def execute(self, command: ExtractGameResultCommand) -> GameResult:
        """
        Execute the use case to extract game results.
        :param command: The command containing the draw date.
        :return: The extracted game result.
        """
        try:
            # Store the game result in the database
            game_result = self.game_repository.create(
                command=command,
                db_session=self.session,
            )

            return game_result
        finally:
            if self.session is not None:
                self.session.close()
