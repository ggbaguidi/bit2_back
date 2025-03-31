from bit2_api.core.ports.database_client_repository import IDatabaseClientRepository

from .session import SessionLocal

"""
Module used to get CSV db session
"""


class DatabaseClient(IDatabaseClientRepository):
    """
    Class used to get CSV db session
    """

    def get_db_session(self) -> SessionLocal:
        """
        Main function to get CSV session
        """
        csv_session = SessionLocal()
        csv_session.current_user_id = None
        if csv_session:
            return csv_session
