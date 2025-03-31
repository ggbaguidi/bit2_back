import csv
import os
from typing import Any, Dict, List

from bit2_api.core.domains.utils import get_env_variable

"""
Engine and session for CSV storage
"""


# Get the base directory for CSV files
CSV_BASE_DIR = get_env_variable("CSV_BASE_DIR", default="./data")


class CSVEngine:
    """Engine for CSV operations"""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def get_file_path(self, table_name: str) -> str:
        """Get the full path for a CSV file"""
        return os.path.join(self.base_dir, f"{table_name}.csv")

    def read_all(self, table_name: str) -> List[Dict[str, Any]]:
        """Read all rows from a CSV file"""
        file_path = self.get_file_path(table_name)
        if not os.path.exists(file_path):
            return []

        with open(file_path, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            return list(reader)

    def write_rows(self, table_name: str, rows: List[Dict[str, Any]], mode: str = "a"):
        """Write rows to a CSV file"""
        file_path = self.get_file_path(table_name)
        file_exists = os.path.exists(file_path)

        with open(file_path, mode, newline="") as csvfile:
            if rows:
                fieldnames = list(rows[0].keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                if not file_exists or mode == "w":
                    writer.writeheader()

                writer.writerows(rows)


class CSVSession:
    """Session for CSV operations"""

    def __init__(self, engine: CSVEngine, autocommit=False, autoflush=False):
        self.engine = engine
        self._pending_writes: Dict[str, List[Dict[str, Any]]] = {}
        self._pending_deletes: Dict[str, List[int]] = {}
        self._autocommit = autocommit

    def add(self, table_name: str, data: Dict[str, Any]):
        """Add a row to be written during commit"""
        if table_name not in self._pending_writes:
            self._pending_writes[table_name] = []

        self._pending_writes[table_name].append(data)

        if self._autocommit:
            self.commit()

    def query(self, table_name: str) -> List[Dict[str, Any]]:
        """Query all rows from a table"""
        return self.engine.read_all(table_name)

    def commit(self):
        """Commit pending changes to CSV files"""
        for table_name, rows in self._pending_writes.items():
            if rows:
                self.engine.write_rows(table_name, rows)
        self._pending_writes = {}

    def rollback(self):
        """Discard pending changes"""
        self._pending_writes = {}

    def close(self):
        """Close the session"""
        self.rollback()


# Create the engine
engine = CSVEngine(CSV_BASE_DIR)

# Create a session factory similar to SQLAlchemy's sessionmaker
class CSVSessionMaker:
    def __init__(self, autocommit=False, autoflush=False, bind=None):
        self.autocommit = autocommit
        self.autoflush = autoflush
        self.bind = bind

    def __call__(self):
        return CSVSession(
            self.bind, autocommit=self.autocommit, autoflush=self.autoflush
        )


# Create SessionLocal similar to the PostgreSQL version
SessionLocal = CSVSessionMaker(autocommit=False, autoflush=False, bind=engine)
