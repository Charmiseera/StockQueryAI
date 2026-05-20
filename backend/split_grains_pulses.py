import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'mcp_server', 'inventory.db')

def split_grains_pulses():
    conn = sqlite3.connect(DB_PATH)
    
    # Fix the miscategorized Cauliflower first
    conn.execute("UPDATE products SET category = 'Vegetables' WHERE category = 'Grains & Pulses' AND name LIKE '%Cauliflower%'")
    
    # Grains
    grains = [
        "Rice", "Flour", "Oats", "Quinoa", "Cornmeal", "Wheat"
    ]
    
    # Pulses (Lentils, Beans, Chickpeas, etc.)
    pulses = [
        "Lentil", "Bean", "Pea", "Chickpea", "Dal", "Gram"
    ]
    
    # Sugars (moving them out to a more appropriate category)
    sugars = ["Sugar", "Sweetener", "Syrup"]
    
    # Update Grains
    for grain in grains:
        conn.execute(
            "UPDATE products SET category = 'Grains' WHERE category = 'Grains & Pulses' AND name LIKE ?", 
            (f"%{grain}%",)
        )
        
    # Update Pulses
    for pulse in pulses:
        conn.execute(
            "UPDATE products SET category = 'Pulses' WHERE category = 'Grains & Pulses' AND name LIKE ?", 
            (f"%{pulse}%",)
        )
        
    # Update Sugars
    for sugar in sugars:
        conn.execute(
            "UPDATE products SET category = 'Sugars & Sweeteners' WHERE category = 'Grains & Pulses' AND name LIKE ?", 
            (f"%{sugar}%",)
        )
        
    # If anything else is left, default it to Grains
    conn.execute("UPDATE products SET category = 'Grains' WHERE category = 'Grains & Pulses'")

    conn.commit()
    conn.close()
    print("Successfully split 'Grains & Pulses' into 'Grains', 'Pulses', and 'Sugars & Sweeteners'!")

if __name__ == "__main__":
    split_grains_pulses()
