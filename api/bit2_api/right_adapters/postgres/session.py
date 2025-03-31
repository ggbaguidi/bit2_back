"""
Engine and session db module
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bit2_api.core.domains.utils import get_env_variable

SQLALCHEMY_DATABASE_URL = get_env_variable("DATABASE_URL")
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
