# pylint: disable=arguments-renamed
from datetime import datetime
from uuid import uuid4

from bit2_api.core.domains.commands import ExtractGameResultCommand
from bit2_api.core.domains.models import GameResult as GameResultModel
from bit2_api.core.domains.utils.enums import GameTypeEnum
from bit2_api.core.ports import IGameResultRepository
from bit2_api.core.ports.session import ISession
from bit2_api.right_adapters.postgres.models import GameResult

from .base_repository import BaseRepository


class GameResultRepository(BaseRepository[GameResult], IGameResultRepository):
    """Repository for game results in PostgreSQL"""

    def __init__(self):
        super().__init__(GameResult)

    def get_by_draw_date(self, draw_date: datetime, db_session: ISession):
        """Get a game result by its draw date"""
        result = (
            db_session.query(GameResult)
            .filter(GameResult.draw_date == draw_date)
            .first()
        )
        if result:
            return self.to_model(result)
        return None

    def get_by_type(self, game_type: GameTypeEnum, db_session: ISession):
        """Get game results by game type"""
        results = (
            db_session.query(GameResult)
            .filter(GameResult.type == game_type.value)
            .all()
        )
        return [self.to_model(result) for result in results]

    def get_all(self, db_session: ISession):
        """Get all game results"""
        results = db_session.query(GameResult).all()
        return [self.to_model(result) for result in results]

    def create(self, command: ExtractGameResultCommand, db_session: ISession):
        """Create a game result"""
        game_result = GameResult(
            id=str(uuid4()),
            draw_date=command.draw_date,
            numbers=command.numbers,
            bonus=command.bonus,
            type=command.type.value,
        )
        db_session.add(game_result)
        db_session.flush()
        return self.to_model(game_result)

    def delete(
        self, draw_date: datetime, game_type: GameTypeEnum, db_session: ISession
    ):
        """Delete a game result"""
        game_result = (
            db_session.query(GameResult)
            .filter(
                GameResult.draw_date == draw_date, GameResult.type == game_type.value
            )
            .first()
        )
        if game_result:
            db_session.delete(game_result)
            db_session.flush()

    @staticmethod
    def to_model(db_model):
        """Convert database model to domain model"""
        return GameResultModel(
            draw_date=db_model.draw_date,
            numbers=db_model.numbers,
            bonus=db_model.bonus,
            type=GameTypeEnum(db_model.type),
        )
