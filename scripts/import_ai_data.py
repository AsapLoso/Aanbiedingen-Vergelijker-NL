import sqlite3
import os
import json
import sys
import shutil

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import DB_PATH

# New DB Path
CATEGORIZED_DB_PATH = os.path.join(os.path.dirname(DB_PATH), 'flyers_categorized.db')

def import_ai_data():
    scripts_dir = os.path.dirname(__file__)
    
    # Find all prompt_X.txt files
    prompt_files = [f for f in os.listdir(scripts_dir) if f.startswith('prompt_') and f.endswith('.txt')]
    
    if not prompt_files:
        print("No 'prompt_X.txt' files found in scripts directory.")
        return

    all_data = []
    
    # 1. Read JSON from all prompt files
    for p_file in prompt_files:
        full_path = os.path.join(scripts_dir, p_file)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            # Try to find JSON list
            start = content.find('[')
            end = content.rfind(']')
            
            if start != -1 and end != -1:
                json_str = content[start:end+1]
                data = json.loads(json_str)
                all_data.extend(data)
                print(f"Loaded {len(data)} items from {p_file}")
            else:
                # Maybe it's just JSON
                data = json.loads(content)
                if isinstance(data, list):
                    all_data.extend(data)
                    print(f"Loaded {len(data)} items from {p_file}")
                else:
                    print(f"Skipping {p_file}: Content is not a JSON list.")
                
        except json.JSONDecodeError:
            print(f"Skipping {p_file}: Invalid JSON (did you overwrite it with AI response?)")
        except Exception as e:
            print(f"Error reading {p_file}: {e}")

    if not all_data:
        print("No valid data found to import.")
        return

    # 2. Create/Update Categorized DB
    print(f"Target Database: {CATEGORIZED_DB_PATH}")
    
    # Always copy fresh from original to ensure we have latest data? 
    # Or only if not exists? User said "make new database! which copies this original one".
    # Let's copy if it doesn't exist, or maybe we should ask? 
    # For safety, let's assume we want to work on a copy. 
    # If we run this multiple times, we might want to keep existing categorizations...
    # But the user said "creates new DB to not overwrite the old one".
    
    if not os.path.exists(CATEGORIZED_DB_PATH):
        print("Creating new categorized database (copying original)...")
        shutil.copy2(DB_PATH, CATEGORIZED_DB_PATH)
    else:
        print("Updating existing categorized database...")

    conn = sqlite3.connect(CATEGORIZED_DB_PATH)
    c = conn.cursor()
    
    # 3. Ensure columns exist
    try:
        c.execute("SELECT category, standardized_name FROM products LIMIT 1")
    except sqlite3.OperationalError:
        print("Adding new columns to categorized database...")
        try:
            c.execute("ALTER TABLE products ADD COLUMN category TEXT")
        except: pass
        try:
            c.execute("ALTER TABLE products ADD COLUMN standardized_name TEXT")
        except: pass
    
    # 4. Update Data
    count = 0
    for item in all_data:
        orig_name = item.get('original_name') or item.get('product_name') # Support both keys just in case
        std_name = item.get('standardized_name')
        cat = item.get('category')
        
        if orig_name and std_name and cat:
            c.execute("""
                UPDATE products 
                SET standardized_name = ?, category = ? 
                WHERE product_name = ?
            """, (std_name, cat, orig_name))
            count += c.rowcount
            
    conn.commit()
    conn.close()
    
    print(f"Successfully updated {count} records in {CATEGORIZED_DB_PATH}")
    print("Now run 'web/generate.py' to see the results (it will use the new DB).")

if __name__ == "__main__":
    import_ai_data()
