"""
server.py — StockQuery AI MCP Server

Exposes all inventory tools via JSON-RPC.
Runs as a standalone HTTP service (port 8001) by default,
or stdio (for Claude Desktop) when MCP_TRANSPORT=stdio.
"""

import sqlite3
import os
import logging

from mcp.server.fastmcp import FastMCP

# ─── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MCP-SERVER] %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────
DB_PATH   = os.path.join(os.path.dirname(__file__), "inventory.db")
MCP_HOST  = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT  = int(os.getenv("MCP_PORT", "8001"))

mcp = FastMCP(
    "StockQuery Inventory Server",
    host=MCP_HOST,
    port=MCP_PORT,
    streamable_http_path="/mcp",
)


# ─── DB Helpers ──────────────────────────────────────────────
def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _rows(cursor_rows) -> list[dict]:
    return [dict(r) for r in cursor_rows]


# ─────────────────────────────────────────────────────────────
# Tool 1: Search by name (partial match)
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def query_inventory_db(product_name: str) -> list[dict]:
    """
    Search inventory for products whose name contains the given string.
    Use this when the user asks about a specific product by name.
    Returns a list of matching product records (empty list = not found).
    """
    log.info(f"[DB] query_inventory_db | name LIKE '%{product_name}%'")
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE name LIKE ? ORDER BY name",
        (f"%{product_name}%",),
    ).fetchall()
    conn.close()
    result = _rows(rows)
    log.info(f"[DB] query_inventory_db | {len(result)} match(es) for '{product_name}'")
    return result


# ─────────────────────────────────────────────────────────────
# Tool 2: Get product by numeric ID
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_product_details(product_id: int) -> dict:
    """
    Retrieve the complete record for a single product by its numeric ID.
    Use this when the user asks for details of a specific product ID.
    Returns an empty dict {} if the product is not found.
    """
    log.info(f"[DB] get_product_details | id={product_id}")
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM products WHERE id = ?", (product_id,)
    ).fetchone()
    conn.close()
    result = dict(row) if row else {}
    if result:
        log.info(f"[DB] get_product_details | found: '{result.get('name')}'")
    else:
        log.warning(f"[DB] get_product_details | no product with id={product_id}")
    return result


# ─────────────────────────────────────────────────────────────
# Tool 3: Advanced search with filters & sorting
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def search_inventory(
    name: str = None,
    category: str = None,
    max_price: float = None,
    min_price: float = None,
    stock_threshold: int = None,
    sort_by: str = None,
) -> list[dict]:
    """
    Search products with optional filters and sorting.
    - name: partial name match
    - category: partial category match
    - max_price / min_price: price range filter
    - stock_threshold: return items with stock <= this value
    - sort_by: price_asc | price_desc | stock_asc | stock_desc
    Returns empty list if no products match.
    """
    log.info(
        f"[DB] search_inventory | name={name!r} category={category!r} "
        f"price=[{min_price},{max_price}] stock_threshold={stock_threshold} sort={sort_by}"
    )
    conn = _get_conn()
    query  = "SELECT * FROM products WHERE 1=1"
    params = []

    if name:
        query += " AND name LIKE ?"
        params.append(f"%{name}%")
    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    if stock_threshold is not None:
        query += " AND stock <= ?"
        params.append(stock_threshold)

    sort_map = {
        "price_asc":  "ORDER BY price ASC",
        "price_desc": "ORDER BY price DESC",
        "stock_asc":  "ORDER BY stock ASC",
        "stock_desc": "ORDER BY stock DESC",
    }
    query += f" {sort_map.get(sort_by, 'ORDER BY name ASC')}"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = _rows(rows)
    log.info(f"[DB] search_inventory | {len(result)} result(s)")
    return result


# ─────────────────────────────────────────────────────────────
# Tool 4: Low-stock alert
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_low_stock_items(threshold: int = 10) -> list[dict]:
    """
    Return all products whose current stock is below the given threshold.
    Default threshold is 10 units. Ordered by stock ascending.
    """
    log.info(f"[DB] get_low_stock_items | stock < {threshold}")
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE stock < ? ORDER BY stock ASC",
        (threshold,),
    ).fetchall()
    conn.close()
    result = _rows(rows)
    log.info(f"[DB] get_low_stock_items | {len(result)} item(s) below threshold")
    return result


# ─────────────────────────────────────────────────────────────
# Tool 5: All distinct categories
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_all_categories() -> list[str]:
    """
    Return a sorted list of all distinct product categories.
    Use this when the user asks what categories are available.
    """
    log.info("[DB] get_all_categories")
    conn = _get_conn()
    rows = conn.execute(
        "SELECT DISTINCT category FROM products ORDER BY category"
    ).fetchall()
    conn.close()
    result = [r["category"] for r in rows]
    log.info(f"[DB] get_all_categories | {len(result)} categories")
    return result


# ─────────────────────────────────────────────────────────────
# Tool 6: Products by category
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_products_by_category(category: str) -> list[dict]:
    """
    Return all products in a specific category (case-insensitive partial match).
    """
    log.info(f"[DB] get_products_by_category | category='{category}'")
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM products WHERE category LIKE ? ORDER BY name",
        (category,),
    ).fetchall()
    conn.close()
    result = _rows(rows)
    log.info(f"[DB] get_products_by_category | {len(result)} product(s)")
    return result


# ─────────────────────────────────────────────────────────────
# Tool 7: Inventory analytics (totals + extremes)
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_inventory_analytics() -> dict:
    """
    High-level inventory statistics: total products, total stock,
    total value, average price, most expensive and cheapest product.
    """
    log.info("[DB] get_inventory_analytics")
    conn = _get_conn()
    stats = conn.execute("""
        SELECT
            COUNT(*) as total_products,
            SUM(stock) as total_items,
            ROUND(SUM(price * stock), 2) as total_inventory_value,
            ROUND(AVG(price), 2) as average_price
        FROM products
    """).fetchone()
    extremes = conn.execute("""
        SELECT
            (SELECT name FROM products ORDER BY price DESC LIMIT 1) as most_expensive,
            (SELECT name FROM products ORDER BY price ASC  LIMIT 1) as cheapest
    """).fetchone()
    conn.close()
    result = {**dict(stats), **dict(extremes)}
    log.info(
        f"[DB] get_inventory_analytics | {result.get('total_products')} products, "
        f"value=${result.get('total_inventory_value')}"
    )
    return result


# ─────────────────────────────────────────────────────────────
# Tool 8: Per-category analytics
# ─────────────────────────────────────────────────────────────
@mcp.tool()
def get_category_analytics() -> list[dict]:
    """
    Per-category breakdown: product count, total stock, avg price.
    Ordered by product count descending.
    """
    log.info("[DB] get_category_analytics")
    conn = _get_conn()
    rows = conn.execute("""
        SELECT
            category,
            COUNT(*) as product_count,
            SUM(stock) as total_stock,
            ROUND(AVG(price), 2) as avg_price
        FROM products
        GROUP BY category
        ORDER BY product_count DESC
    """).fetchall()
    conn.close()
    result = _rows(rows)
    log.info(f"[DB] get_category_analytics | {len(result)} categories")
    return result


# ─────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "http")
    if transport == "stdio":
        log.info("Starting MCP server — stdio transport (Claude Desktop mode)")
        mcp.run(transport="stdio")
    else:
        log.info(f"Starting MCP server — streamable-http on {MCP_HOST}:{MCP_PORT}/mcp")
        mcp.run(transport="streamable-http")
