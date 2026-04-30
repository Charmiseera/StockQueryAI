import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'mcp_server', 'inventory.db')

def split_categories():
    conn = sqlite3.connect(DB_PATH)
    
    # Define known fruits
    fruits = [
        "Apple", "Apricot", "Banana", "Blueberries", "Cherry", "Coconut", 
        "Grapes", "Kiwi", "Lemon", "Lime", "Mango", "Orange", "Papaya", 
        "Peach", "Pear", "Pineapple", "Plum", "Pomegranate", "Strawberries", 
        "Watermelon"
    ]
    
    # Define known vegetables
    vegetables = [
        "Asparagus", "Bell Pepper", "Broccoli", "Cabbage", "Carrot", 
        "Cauliflower", "Cucumber", "Eggplant", "Garlic", "Green Beans", 
        "Kale", "Lettuce", "Mushrooms", "Onion", "Peas", "Potato", 
        "Spinach", "Sweet Potato", "Tomato", "Zucchini"
    ]
    
    # Update Fruits
    for fruit in fruits:
        conn.execute(
            "UPDATE products SET category = 'Fruits' WHERE category = 'Fruits & Vegetables' AND name LIKE ?", 
            (f"%{fruit}%",)
        )
        
    # Update Vegetables
    for veg in vegetables:
        conn.execute(
            "UPDATE products SET category = 'Vegetables' WHERE category = 'Fruits & Vegetables' AND name LIKE ?", 
            (f"%{veg}%",)
        )
        
    # There is a row for "Greek Yogurt" which was incorrectly categorized as Fruits & Vegetables in the dataset. Let's fix that too.
    conn.execute(
        "UPDATE products SET category = 'Dairy' WHERE category = 'Fruits & Vegetables' AND name LIKE '%Yogurt%'"
    )

    # If anything else is left, we can just leave it as is or default to Vegetables.
    # Let's check if there are any stragglers:
    remaining = conn.execute("SELECT DISTINCT name FROM products WHERE category = 'Fruits & Vegetables'").fetchall()
    if remaining:
        print("Leftover Items in 'Fruits & Vegetables':", [r[0] for r in remaining])
        # If any remain, just default them to Vegetables for the sake of splitting cleanly
        conn.execute("UPDATE products SET category = 'Vegetables' WHERE category = 'Fruits & Vegetables'")

    conn.commit()
    conn.close()
    print("Successfully split 'Fruits & Vegetables' into 'Fruits' and 'Vegetables' in the database!")

if __name__ == "__main__":
    split_categories()
