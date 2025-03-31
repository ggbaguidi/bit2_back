"""
Generic abstract CRUD
"""

from abc import ABC
from typing import Generic, Type, TypeVar
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from bit2_api.right_adapters.postgres.models.base_model import BaseModel

# pylint: disable=invalid-name
ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType], ABC):
    """
    Main class
    """

    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read
        *Parameters*
        * model: A SQLAlchemy model class
        """
        self.model = model

    @staticmethod
    def to_model(item: ModelType):
        """Method to convert from model db object to domain model"""
        raise NotImplementedError

    def get_all(self, db_session: Session):
        """
        Get all method.
        """
        return [self.to_model(item) for item in db_session.query(self.model).all()]

    def get_by_id(self, item_id: UUID, db_session: Session):
        """
        Get by ID method
        """
        obj = db_session.query(self.model).filter(self.model.id == item_id).first()
        if obj is not None:
            return self.to_model(obj)
        return None

    def get_attribute_by_id(
        self, item_id: UUID, attribute_name: str, db_session: Session
    ):
        """
        Get a property for an ID method.
        """
        row = (
            db_session.query(getattr(self.model, attribute_name))
            .filter(self.model.id == item_id)
            .first()
        )
        if row is not None:
            return row[0]

        return None

    def exists(self, item_id: UUID, db_session: Session) -> bool:
        """
        Checks if object id exists in database.
        """
        return db_session.query(
            db_session.query(self.model.id).filter_by(id=item_id).exists()
        ).scalar()

    def create(self, obj: dict, db_session: Session):
        """
        Create method
        """
        db_obj = self.model(**obj, id=uuid4())
        db_session.add(db_obj)
        db_session.commit()
        db_session.refresh(db_obj)

        return self.to_model(db_obj)

    def update(self, id_, obj: dict, db_session: Session):
        """
        Update method
        """
        db_obj = db_session.query(self.model).filter(self.model.id == id_).first()
        for key in obj.keys():
            setattr(db_obj, key, obj[key])
        db_session.add(db_obj)
        db_session.commit()

        return self.to_model(db_obj)
