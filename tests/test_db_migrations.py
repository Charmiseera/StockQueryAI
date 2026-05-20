"""
tests/test_db_migrations.py — Tests for database schema creation.
"""

import sqlite3
import pytest
from db.migrations import run_migrations


def test_schema_creates_all_tables(test_db):
    tables = {row[0] for row in test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    assert "users" in tables
    assert "products" in tables
    assert "stock_audit_log" in tables


def test_products_has_user_id_not_null(test_db):
    """user_id must be NOT NULL — no dangerous DEFAULT 1."""
    with pytest.raises(sqlite3.IntegrityError):
        test_db.execute(
            "INSERT INTO products (name, category, stock, price, supplier) VALUES (?,?,?,?,?)",
            ("Apple", "Fruit", 10, 1.5, "FarmCo"),
        )


def test_indexes_exist(test_db):
    indexes = {row[0] for row in test_db.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()}
    assert "idx_products_user_id" in indexes
    assert "idx_products_category" in indexes
    assert "idx_products_name" in indexes


def test_stock_constraint(test_db):
    """Negative stock must be rejected by the CHECK constraint."""
    # First create a valid user
    test_db.execute(
        "INSERT INTO users (username, email, hashed_password) VALUES (?,?,?)",
        ("u1", "u1@example.com", "hash"),
    )
    test_db.commit()
    user_id = test_db.execute("SELECT id FROM users WHERE username='u1'").fetchone()["id"]

    with pytest.raises(sqlite3.IntegrityError):
        test_db.execute(
            "INSERT INTO products (user_id, name, category, stock, price, supplier) VALUES (?,?,?,?,?,?)",
            (user_id, "Widget", "Tools", -1, 9.99, "SupplierA"),
        )
