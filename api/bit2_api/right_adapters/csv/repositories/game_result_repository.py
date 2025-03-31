from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from bit2_api.core.domains.commands import ExtractGameResultCommand
from bit2_api.core.domains.models import GameResult as GameResultModel
from bit2_api.core.domains.utils.enums import GameTypeEnum
from bit2_api.core.ports import IGameResultRepository
from bit2_api.right_adapters.csv.session import CSVSession

from .base_repository import BaseRepository

# pylint: disable=arguments-renamed


class GameResultRepository(BaseRepository[GameResultModel], IGameResultRepository):
    """Repository for game results in CSV"""

    def __init__(self):
        super().__init__(f"{datetime.now()}-game_results")

    @staticmethod
    def to_model(item: Dict[str, Any]) -> GameResultModel:
        """Convert from CSV dictionary to domain model"""
        return GameResultModel(
            draw_date=datetime.fromisoformat(item["draw_date"]),
            numbers=item["numbers"],
            bonus=item["bonus"],
            type=GameTypeEnum(item["type"]),
        )

    @staticmethod
    def to_dict(model: GameResultModel) -> Dict[str, Any]:
        """Convert from domain model to CSV dictionary"""
        return {
            "draw_date": model.draw_date.isoformat(),
            "numbers": model.numbers,
            "bonus": model.bonus,
            "type": model.type.value,
        }

    def get_by_draw_date(self, draw_date: datetime, db_session: CSVSession):
        """Get a game result by its draw date"""
        rows = db_session.query(self.table_name)
        for row in rows:
            if datetime.fromisoformat(row["draw_date"]) == draw_date:
                return self.to_model(row)
        return None

    def get_by_type(self, game_type: GameTypeEnum, db_session: CSVSession):
        """Get game results by game type"""
        rows = db_session.query(self.table_name)
        results = [row for row in rows if row["type"] == game_type.value]
        return [self.to_model(result) for result in results]

    def get_all(self, db_session: CSVSession):
        """Get all game results"""
        rows = db_session.query(self.table_name)
        return [self.to_model(row) for row in rows]

    def create(self, command: ExtractGameResultCommand, db_session: CSVSession):
        """Create a game result"""
        game_result_dict = {
            "id": str(uuid4()),
            "draw_date": command.draw_date.isoformat(),
            "numbers": command.numbers,
            "bonus": command.bonus,
            "type": command.type.value,
        }
        return super().create(game_result_dict, db_session)

    def delete(
        self, draw_date: datetime, game_type: GameTypeEnum, db_session: CSVSession
    ):
        """Delete a game result"""
        rows = db_session.query(self.table_name)
        updated_rows = []

        for row in rows:
            # Keep rows that don't match the criteria for deletion
            if (
                datetime.fromisoformat(row["draw_date"]) != draw_date
                or row["type"] != game_type.value
            ):
                updated_rows.append(row)

        # Write all remaining rows back to the file (effectively deleting the matching ones)
        if len(updated_rows) < len(rows):
            db_session.engine.write_rows(self.table_name, updated_rows, mode="w")
