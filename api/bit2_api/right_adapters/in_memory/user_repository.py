# pylint: disable=dangerous-default-value
from datetime import date
from typing import List

from phytov_api.core.domain.commands import CreateUserCommand
from phytov_api.core.domain.models import User
from phytov_api.core.domain.utils.datetime import date_to_string, string_to_date
from phytov_api.core.domain.utils.enums import CountryEnum, UserRoleEnum
from phytov_api.core.ports import IUserRepository


class InMemoryUserRepository(IUserRepository):
    def __init__(
        self,
        users: List[dict] = [],
    ) -> None:
        self.users = users

    def get_by_phone_number(self, phone_number, db_session=None) -> User:
        for user in self.users:
            if user["phone_number"] == phone_number:
                return self.to_model(user)
        return None

    def get_by_email(self, email, db_session=None) -> User:
        """Method to get a user by its email"""
        for user in self.users:
            if user["email"] == email:
                return self.to_model(user)
        return None

    def create(self, command: CreateUserCommand, db_session=None) -> User:
        user = User(
            id_="00000000-0000-0000-0001-000000000000",
            creation_date=date.today(),
            email=command.email,
            password=command.password,
            phone_number=command.phone_number,
            first_name=command.first_name,
            last_name=command.last_name,
            birth_date=command.birth_date,
            address=command.address if command.address else None,
            country=command.country.value if command.country else None,
            city=command.city,
            roles=command.roles,
        )
        self.users.append(self.from_model(user))
        return user

    def update(self, id_, obj, db_session=None) -> User:
        for user in self.users:
            if user["id"] == id_:
                for key in obj.keys():
                    user[key] = obj[key]
                return self.to_model(user)
        return None

    @staticmethod
    def to_model(item) -> User:
        """Method to convert from dict to domain model"""
        return User(
            id_=item["id"],
            creation_date=(
                string_to_date(item["created_at"]) if item["created_at"] else None
            ),
            email=item["email"],
            phone_number=item["phone_number"],
            password=item["password"],
            first_name=item["first_name"],
            last_name=item["last_name"],
            roles=(
                [UserRoleEnum[role] for role in item["roles"]]
                if item["roles"] is not None
                else None
            ),
            birth_date=string_to_date(item["birth_date"]),
            address=item["address"] if "address" in item else None,
            country=(
                CountryEnum[item["country"]]
                if "country" in item and item["country"] is not None
                else None
            ),
            city=item["city"] if "city" in item else None,
        )

    @staticmethod
    def from_model(item: User) -> dict:
        """Method to convert from domain model to dict"""
        return {
            "id": item.id_,
            "created_at": (
                date_to_string(item.creation_date) if item.creation_date else None
            ),
            "email": item.email,
            "phone_number": item.phone_number,
            "password": item.password,
            "first_name": item.first_name,
            "last_name": item.last_name,
            "roles": list(item.roles) if item.roles is not None else None,
            "birth_date": item.birth_date,
            "address": item.address,
            "country": item.country if item.country else None,
            "city": item.city,
        }
