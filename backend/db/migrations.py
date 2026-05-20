"""
db/migrations.py — Schema bootstrap using SQLAlchemy.
"""

import logging
from sqlalchemy import Engine
from db.models import Base

log = logging.getLogger(__name__)


def run_migrations(engine: Engine) -> None:
    """Apply all schema migrations via SQLAlchemy."""
    log.info("[DB] Creating database tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    log.info("[DB] Schema migrations complete.")

