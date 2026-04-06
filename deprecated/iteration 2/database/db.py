import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'flyers.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS flyers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store TEXT NOT NULL,
            week INTEGER NOT NULL,
            year INTEGER NOT NULL,
            type TEXT NOT NULL, -- 'pdf' or 'images'
            path TEXT NOT NULL, -- Path to file or directory
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store, week, year)
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store TEXT NOT NULL,
            week INTEGER NOT NULL,
            year INTEGER NOT NULL,
            page_number INTEGER,
            brand TEXT,
            product_name TEXT,
            amount INTEGER,
            deal_price REAL,
            original_price_text TEXT,
            box_2d TEXT, -- JSON string of [ymin, xmin, ymax, xmax]
            category TEXT, -- High-level category
            standardized_name TEXT, -- Common name for grouping
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migration: Check if box_2d exists, if not add it
    try:
        c.execute("SELECT box_2d FROM products LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE products ADD COLUMN box_2d TEXT")

    # Migration: Check if category exists
    try:
        c.execute("SELECT category FROM products LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE products ADD COLUMN category TEXT")
        c.execute("ALTER TABLE products ADD COLUMN standardized_name TEXT")
        
    conn.commit()
    conn.close()

def add_flyer(store, week, year, flyer_type, path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR REPLACE INTO flyers (store, week, year, type, path)
            VALUES (?, ?, ?, ?, ?)
        ''', (store, week, year, flyer_type, path))
        conn.commit()
    except Exception as e:
        print(f"Error adding flyer to DB: {e}")
    finally:
        conn.close()

def get_flyers(week, year):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT * FROM flyers WHERE week = ? AND year = ?
    ''', (week, year))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_products(store, week, year, page_number=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    query = "SELECT * FROM products WHERE store = ? AND week = ? AND year = ?"
    params = [store, week, year]
    
    if page_number is not None:
        query += " AND page_number = ?"
        params.append(page_number)
        
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_product(store, week, year, page_number, product_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Serialize box_2d if present
    box_2d = product_data.get('box_2d')
    if isinstance(box_2d, list):
        import json
        box_2d = json.dumps(box_2d)
        
    try:
        c.execute('''
            INSERT INTO products (store, week, year, page_number, brand, product_name, amount, deal_price, original_price_text, box_2d, category, standardized_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (store, week, year, page_number, 
              product_data.get('brand'), 
              product_data.get('product_name'), 
              product_data.get('amount'), 
              product_data.get('deal_price'), 
              product_data.get('original_price_text'),
              box_2d,
              product_data.get('category'),
              product_data.get('standardized_name')))
        conn.commit()
    except Exception as e:
        print(f"Error adding product to DB: {e}")
    finally:
        conn.close()
