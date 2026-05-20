"""
db/connection.py — Centralized SQLAlchemy connection factory.

Single source of truth for DB connection settings.
Now uses SQLAlchemy for PostgreSQL compatibility.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://stockquery:stockpassword@localhost:5432/stockquery_db"
)

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Automatically ping connections to detect stale ones
    pool_size=10,        # Number of connections to keep open
    max_overflow=20,     # Allow up to 20 additional connections if needed
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields an ORM Session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
