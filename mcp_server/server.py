"""
server.py — StockQuery AI MCP Server
Exposes 5 inventory tools to Claude via the MCP stdio protocol.
"""

import sqlite3
import os
from mcp.server.fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(__file__), 'inventory.db')

mcp = FastMCP("StockQuery Inventory Server")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


# ─────────────────────────────────────────────────────────────
# Tool 1: Search products by name (partial match)
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def query_inventory_db(product_name: str) -> list[dict]:
    """
    Search inventory for products whose name contains the given string.
    Use this when the user asks about a specific product by name.
    Returns a list of matching product records.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE name LIKE ? ORDER BY name",
        (f"%{product_name}%",)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────
# Tool 2: Get full details of one product by ID
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_product_details(product_id: int) -> dict:
    """
    Retrieve the complete record for a single product by its numeric ID.
    Use this when the user asks for details of a specific product ID.
    Returns an empty dict if the product is not found.
    """
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else {}


# ─────────────────────────────────────────────────────────────
# Tool 3: Find all products below a stock threshold
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_low_stock_items(threshold: int = 10) -> list[dict]:
    """
    Return all products whose current stock is below the given threshold.
    Use this for restocking alerts or when the user asks about low stock.
    Default threshold is 10 units.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE stock < ? ORDER BY stock ASC",
        (threshold,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────
# Tool 4: List all distinct product categories
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_all_categories() -> list[str]:
    """
    Return a list of all distinct product categories in the inventory.
    Use this when the user asks what categories or departments are available.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()
    conn.close()
    return [r["category"] for r in rows]


# ─────────────────────────────────────────────────────────────
# Tool 5: Filter products by category
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_products_by_category(category: str) -> list[dict]:
    """
    Return all products that belong to a specific category.
    Use this when the user wants to browse a particular department or category.
    The match is case-insensitive.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE category LIKE ? ORDER BY name",
        (category,)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


if __name__ == '__main__':
    mcp.run()
