# pylint: disable=dangerous-default-value
from typing import Dict, List, Optional
from uuid import uuid4

from phytov_api.core.ports import ISessionTokenRepository


class InMemorySessionTokenRepository(ISessionTokenRepository):
    def __init__(self, session_tokens: List[dict] = []) -> None:
        self.session_tokens = session_tokens

    def generate(self, username: str, db_session=None) -> str:
        session_token: Dict = {
            "token": f"token:{username}_{uuid4()}",
            "username": username,
        }
        self.session_tokens.append(session_token)

        return self.to_model(session_token)

    def get_linked_username(self, token: str, db_session=None) -> Optional[str]:
        for session_token in self.session_tokens:
            if session_token["token"] == token:
                return session_token["username"]
        return None

    def revoke(self, token: str, db_session=None) -> bool:
        """
        Method to revoke a token. Returns true if the token was found and
        revoked. False otherwise.
        """
        for session_token in self.session_tokens:
            if session_token["token"] == token:
                self.session_tokens.remove(session_token)
                return True
        return False

    def revoke_all(self, username: str, db_session=None) -> None:
        for session_token in self.session_tokens:
            if session_token["username"] == username:
                self.session_tokens.remove(session_token)

    @staticmethod
    def to_model(session_token: Dict) -> str:
        return session_token["token"]
