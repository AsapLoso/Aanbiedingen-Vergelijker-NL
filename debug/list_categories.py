import sqlite3
import os

# Define the path to the database
# Assuming this script is in the 'scripts' folder and the database is in 'database' folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'flyers.db')

def list_categories():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT category FROM products ORDER BY category")
        categories = cursor.fetchall()
        
        print("\n--- Categories in Database ---")
        if not categories:
            print("No categories found.")
        else:
            for cat in categories:
                # cat is a tuple, e.g., ('Vegetables',)
                print(f"- {cat[0]}")
        print("------------------------------\n")
        
        conn.close()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    list_categories()
