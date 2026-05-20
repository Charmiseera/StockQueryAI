"""
tests/conftest.py — Shared pytest fixtures for all test modules.

Uses an in-memory SQLite database so tests never touch the real inventory.db.
"""

import os
import sys
import pytest
from pathlib import Path

# Ensure backend/ is on the path before importing app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Set required environment variables BEFORE app import
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production-32chars!")
os.environ.setdefault("NEBIUS_API_KEY", "test-key")

import sqlite3
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI
from fastapi.testclient import TestClient

from db.migrations import run_migrations


@pytest.fixture(scope="function")
def test_db(tmp_path):
    """
    Return an in-memory SQLite connection with the full schema applied.
    Each test function gets a fresh database.
    """
    db_file = tmp_path / "test_inventory.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    run_migrations(conn)
    yield conn
    conn.close()


@pytest.fixture(scope="function")
def test_db_path(tmp_path):
    """Return a temp path string for tests that need a DB path."""
    db_file = tmp_path / "test_inventory.db"
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    run_migrations(conn)
    conn.close()
    return str(db_file)


@pytest.fixture
def registered_user_credentials():
    return {"username": "testuser", "email": "test@example.com", "password": "Password123"}
