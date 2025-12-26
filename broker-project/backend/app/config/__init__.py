"""
Configuration Module
====================
Exports configuration settings and database connections.
"""

from .settings import settings, Settings
from .database import (
    DatabaseManager,
    db_manager,
    get_db,
    get_broker_collection
)

__all__ = [
    'settings',
    'Settings',
    'DatabaseManager',
    'db_manager',
    'get_db',
    'get_broker_collection'
]
