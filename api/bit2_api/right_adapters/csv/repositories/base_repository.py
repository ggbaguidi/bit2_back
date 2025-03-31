from abc import ABC
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID, uuid4

from bit2_api.right_adapters.csv.session import CSVSession

"""
Generic abstract CRUD for CSV repositories
"""


# Define a type variable for domain models
ModelType = TypeVar("ModelType")
# Define a type variable for CSV data dictionaries
DictType = TypeVar("DictType", bound=Dict[str, Any])


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository for CSV storage with CRUD operations
    """

    def __init__(self, table_name: str):
        """
        Initialize the repository with a table name

        Parameters:
        * table_name: The name of the CSV file (without the .csv extension)
        """
        self.table_name = table_name

    @staticmethod
    def to_model(item: Dict[str, Any]) -> ModelType:
        """Method to convert from CSV dictionary to domain model"""
        raise NotImplementedError

    @staticmethod
    def to_dict(model: ModelType) -> Dict[str, Any]:
        """Method to convert from domain model to CSV dictionary"""
        raise NotImplementedError

    def get_all(self, db_session: CSVSession) -> List[ModelType]:
        """
        Get all records from the CSV file
        """
        rows = db_session.query(self.table_name)
        return [self.to_model(row) for row in rows]

    def get_by_id(self, item_id: UUID, db_session: CSVSession) -> Optional[ModelType]:
        """
        Get a record by ID
        """
        rows = db_session.query(self.table_name)
        for row in rows:
            if row.get("id") == str(item_id):
                return self.to_model(row)
        return None

    def get_attribute_by_id(
        self, item_id: UUID, attribute_name: str, db_session: CSVSession
    ) -> Optional[Any]:
        """
        Get a specific attribute value for a record by ID
        """
        rows = db_session.query(self.table_name)
        for row in rows:
            if row.get("id") == str(item_id):
                return row.get(attribute_name)
        return None

    def exists(self, item_id: UUID, db_session: CSVSession) -> bool:
        """
        Check if a record with the given ID exists
        """
        rows = db_session.query(self.table_name)
        for row in rows:
            if row.get("id") == str(item_id):
                return True
        return False

    def create(self, obj: Dict[str, Any], db_session: CSVSession) -> ModelType:
        """
        Create a new record
        """
        # Create a copy to avoid modifying the original
        data = obj.copy()
        # Generate a new UUID if not provided
        if "id" not in data:
            data["id"] = str(uuid4())

        # Add to the session
        db_session.add(self.table_name, data)
        db_session.commit()

        return self.to_model(data)

    def update(
        self, id_: UUID, obj: Dict[str, Any], db_session: CSVSession
    ) -> Optional[ModelType]:
        """
        Update a record
        """
        rows = db_session.query(self.table_name)
        updated_rows = []
        updated_item = None

        for row in rows:
            if row.get("id") == str(id_):
                # Update the row with new values
                updated_row = row.copy()
                for key, value in obj.items():
                    updated_row[key] = value
                updated_rows.append(updated_row)
                updated_item = updated_row
            else:
                updated_rows.append(row)

        # Write all rows back to the file
        db_session.engine.write_rows(self.table_name, updated_rows, mode="w")

        if updated_item:
            return self.to_model(updated_item)
        return None
