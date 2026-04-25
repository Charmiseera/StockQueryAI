"""
seed_db.py — Creates inventory.db and seeds it with real-like product data.
Supports both custom CSV (Kaggle) and built-in fallback seed data.
Run: python backend/seed_db.py [path/to/kaggle.csv]
"""

import sqlite3
import os
import sys
import csv

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'mcp_server', 'inventory.db')

SEED_PRODUCTS = [
    # (name, category, stock, price, supplier)
    # Dairy
    ("Whole Milk 1L",        "Dairy",         4,   55.00, "FreshFarm Ltd."),
    ("Cheddar Cheese 200g",  "Dairy",        18,  185.00, "DairyBest Co."),
    ("Unsalted Butter 500g", "Dairy",         7,  130.00, "FreshFarm Ltd."),
    ("Greek Yogurt 400g",    "Dairy",        22,   90.00, "NutriDairy Pvt."),
    ("Paneer 250g",          "Dairy",         3,  110.00, "LocalFresh Farms"),

    # Grains
    ("Basmati Rice 1kg",     "Grains",        5,  120.00, "AgroSupply Co."),
    ("Whole Wheat Flour 1kg","Grains",       35,   65.00, "GrainMaster Ltd."),
    ("Rolled Oats 500g",     "Grains",       50,   85.00, "HealthGrain Inc."),
    ("Quinoa 500g",          "Grains",        6,  280.00, "OrganicWorld Co."),
    ("Cornmeal 1kg",         "Grains",       28,   72.00, "AgroSupply Co."),

    # Electronics
    ("USB-C Hub 7-Port",     "Electronics",  12, 1499.00, "TechZone India"),
    ("Bluetooth Speaker 20W","Electronics",  45, 2299.00, "SoundMax Pvt."),
    ("Full HD Webcam 1080p", "Electronics",   8,  999.00, "TechZone India"),
    ("Mechanical Keyboard",  "Electronics",  19, 3499.00, "KeyWorks Ltd."),
    ("Wireless Mouse",       "Electronics",  33,  699.00, "PeriphX Corp."),

    # Snacks
    ("Classic Potato Chips",  "Snacks",      80,   35.00, "SnackWorld Pvt."),
    ("Digestive Biscuits",    "Snacks",      60,   55.00, "BakeBest Co."),
    ("Mixed Nuts 250g",       "Snacks",       9,  220.00, "NutriSnacks Ltd."),
    ("Granola Bars (6 pack)", "Snacks",      42,   95.00, "HealthBite Inc."),
    ("Microwave Popcorn",     "Snacks",       2,   48.00, "SnackWorld Pvt."),

    # Personal Care
    ("Anti-Dandruff Shampoo", "Personal Care",15,  299.00, "CleanCare Pvt."),
    ("Moisturizing Soap",     "Personal Care",70,   55.00, "PureGlow Ltd."),
    ("Whitening Toothpaste",  "Personal Care",40,   89.00, "SmileBright Co."),
    ("Face Wash 100ml",       "Personal Care", 5,  199.00, "CleanCare Pvt."),
    ("Conditioner 200ml",     "Personal Care",11,  245.00, "HairLux Pvt."),
]


def create_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT    NOT NULL,
            category TEXT    NOT NULL,
            stock    INTEGER NOT NULL DEFAULT 0,
            price    REAL    NOT NULL DEFAULT 0.0,
            supplier TEXT    NOT NULL DEFAULT 'Unknown'
        )
    """)
    conn.commit()


def load_from_csv(conn: sqlite3.Connection, csv_path: str) -> int:
    """
    Load products from a Kaggle CSV file.
    Auto-maps common column names to our schema.
    Returns number of rows inserted.
    """
    col_map = {
        'name':     ['product_name', 'name', 'item_name', 'product', 'item', 'description'],
        'category': ['category', 'catagory', 'category_name', 'type', 'department', 'section'],
        'stock':    ['stock', 'quantity', 'stock_quantity', 'qty', 'units', 'inventory'],
        'price':    ['price', 'unit_price', 'selling_price', 'mrp', 'cost'],
        'supplier': ['supplier', 'supplier_name', 'vendor', 'brand', 'manufacturer', 'source'],
    }

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = [h.lower().strip() for h in (reader.fieldnames or [])]

        # Resolve column mapping
        resolved = {}
        for field, candidates in col_map.items():
            for c in candidates:
                if c in headers:
                    resolved[field] = c
                    break

        if 'name' not in resolved:
            print(f"[ERROR] Cannot find a 'name' column in CSV. Headers: {headers}")
            return 0

        rows = 0
        for row in reader:
            lower_row = {k.lower().strip(): v for k, v in row.items()}
            try:
                name     = str(lower_row.get(resolved.get('name', ''), '')).strip()[:200]
                category = str(lower_row.get(resolved.get('category', ''), 'General')).strip()[:100] or 'General'
                stock    = int(float(lower_row.get(resolved.get('stock', ''), 0) or 0))
                
                raw_price = str(lower_row.get(resolved.get('price', ''), '0.0')).replace('$', '').replace(',', '').strip()
                price    = float(raw_price or 0.0)
                supplier = str(lower_row.get(resolved.get('supplier', ''), 'Unknown')).strip()[:100] or 'Unknown'

                if not name:
                    continue

                conn.execute(
                    "INSERT INTO products (name, category, stock, price, supplier) VALUES (?, ?, ?, ?, ?)",
                    (name, category, stock, round(price, 2), supplier)
                )
                rows += 1
            except (ValueError, KeyError):
                continue  # Skip malformed rows

        conn.commit()
        return rows


def load_builtin_seed(conn: sqlite3.Connection) -> int:
    conn.executemany(
        "INSERT INTO products (name, category, stock, price, supplier) VALUES (?, ?, ?, ?, ?)",
        SEED_PRODUCTS
    )
    conn.commit()
    return len(SEED_PRODUCTS)


def main() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)

    # Clear existing data for a clean seed
    conn.execute("DELETE FROM products")
    conn.commit()

    csv_path = sys.argv[1] if len(sys.argv) > 1 else None

    if csv_path:
        if not os.path.exists(csv_path):
            print(f"[ERROR] CSV not found: {csv_path}")
            sys.exit(1)
        count = load_from_csv(conn, csv_path)
        if count == 0:
            print("[WARN] CSV load failed or empty — falling back to built-in seed data.")
            count = load_builtin_seed(conn)
        else:
            print(f"[OK] Loaded {count} rows from CSV: {csv_path}")
    else:
        count = load_builtin_seed(conn)
        print(f"[OK] Seeded {count} built-in products.")

    conn.close()
    print(f"[OK] Database ready at: {os.path.abspath(DB_PATH)}")

    # Print summary
    conn2 = sqlite3.connect(DB_PATH)
    rows = conn2.execute("SELECT category, COUNT(*) FROM products GROUP BY category").fetchall()
    print("\nInventory Summary:")
    for cat, cnt in rows:
        print(f"   {cat}: {cnt} products")
    total = conn2.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    print(f"\n   Total: {total} products")
    conn2.close()


if __name__ == '__main__':
    main()
