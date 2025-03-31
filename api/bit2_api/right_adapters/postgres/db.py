"""
Module used to get db session
"""

from bit2_api.core.ports.database_client_repository import IDatabaseClientRepository

from .session import SessionLocal


class DatabaseClient(IDatabaseClientRepository):
    """
    Class used to get db session
    """

    def get_db_session(self) -> SessionLocal:
        """
        Main function
        """
        db_session = SessionLocal()
        db_session.current_user_id = None
        with db_session:
            return db_session
