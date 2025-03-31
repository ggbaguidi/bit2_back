"""
This module configures the dependency injection for the application.
"""
import inject

from bit2_api.right_adapters.csv.db import DatabaseClient
from bit2_api.right_adapters.csv.repositories import GameResultRepository
from bit2_api.utils_main.get_dep_inject_config import get_dependencies_injection_config


def configure_injections() -> None:
    """
    Configure the injections for the application.
    This function sets up the dependency injection for the application
    using the inject library.
    """
    inject.configure(
        get_dependencies_injection_config(
            DatabaseClient,
            GameResultRepository,
        )
    )
