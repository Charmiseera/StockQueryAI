import sqlite3
conn = sqlite3.connect('mcp_server/inventory.db')
row = conn.execute("SELECT COUNT(*) FROM products WHERE category = 'Fruits'").fetchone()
print(f"Fruits category count: {row[0]}")
conn.close()
