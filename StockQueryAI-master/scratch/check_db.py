import sqlite3
import os

DB_PATH = "mcp_server/inventory.db"

if not os.path.exists(DB_PATH):
    print(f"File {DB_PATH} not found.")
else:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        row = cursor.fetchone()
        if row:
            print(f"Schema for 'users':\n{row[0]}")
        else:
            print("Table 'users' not found.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
