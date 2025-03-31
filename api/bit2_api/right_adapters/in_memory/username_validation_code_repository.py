# pylint: disable=dangerous-default-value
from typing import Dict, List

from phytov_api.core.domain.commands import CreateValidationCodeCommand
from phytov_api.core.domain.models import UsernameValidationCode
from phytov_api.core.ports import IUsernameValidationCodeRepository


class InMemoryUsernameValidationCodeRepository(IUsernameValidationCodeRepository):
    def __init__(self, username_validation_codes: List[Dict] = []) -> None:
        self.username_validation_codes = username_validation_codes

    def get_by_username(self, username, db_session=None) -> UsernameValidationCode:
        for username_validation_code in self.username_validation_codes:
            if username_validation_code["username"] == username:
                return self.to_model(username_validation_code)
        return None

    def create_or_replace(
        self,
        command: CreateValidationCodeCommand,
        db_session=None,
    ) -> str:
        for username_validation_code in self.username_validation_codes:
            if username_validation_code["username"] == command.username:
                self.username_validation_codes.remove(username_validation_code)
        username_validation_code = UsernameValidationCode(
            username=command.username,
            code=command.code,
            expiration_date=command.expiration_date,
        )
        self.username_validation_codes.append(
            {
                "username": username_validation_code.username,
                "code": username_validation_code.code,
                "expiration_date": username_validation_code.expiration_date,
            }
        )
        return command.code

    @staticmethod
    def to_model(item):
        """Method to convert from dict to domain model"""
        return UsernameValidationCode(
            code=item["code"],
            username=item["username"],
            expiration_date=None,
        )
