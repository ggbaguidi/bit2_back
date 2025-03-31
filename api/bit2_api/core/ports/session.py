from abc import ABC, abstractmethod


class ISession(ABC):
    """Session interface"""

    @abstractmethod
    def close(self) -> None:
        """Closes the session"""
        raise NotImplementedError
