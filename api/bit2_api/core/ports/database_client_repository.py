"""Database client repository interface.
This module defines the interface for a database client repository.
It provides methods for inserting, updating, deleting, and fetching data from the database.
"""
from abc import ABC, abstractmethod

from bit2_api.core.ports.session import ISession


class IDatabaseClientRepository(ABC):
    """Interface for a database client repository."""

    @abstractmethod
    def get_db_session(self) -> ISession:
        """Method to get database session"""
        raise NotImplementedError
