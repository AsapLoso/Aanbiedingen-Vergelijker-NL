import sqlite3
import os
import json
import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'web_deals.db')

def init_web_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS web_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store TEXT NOT NULL,
            week INTEGER NOT NULL,
            year INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            price_text TEXT,
            deal_price REAL,
            original_price REAL,
            unit_size TEXT,
            deal_tag TEXT, -- e.g. "1+1 gratis", "2e halve prijs"
            image_url TEXT,
            valid_start_date TEXT,
            valid_end_date TEXT,
            category TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(store, week, year, product_name, deal_tag)
        )
    ''')
    conn.commit()
    conn.close()

def delete_web_products(store, week, year):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM web_products WHERE store = ? AND week = ? AND year = ?", (store, week, year))
        conn.commit()
        print(f"Deleted existing web products for {store} Week {week}, {year}")
    except Exception as e:
        print(f"Error deleting web products: {e}")
    finally:
        conn.close()

def add_web_product(product_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # We rely on the caller to clear data first, or we can use a better unique constraint.
        # But since we have NULLs in unique columns, SQLite allows duplicates.
        # We could use COALESCE in the unique index, but that's complex.
        # Clearing data is cleaner for a full scrape.
        
        c.execute('''
            INSERT INTO web_products (
                store, week, year, product_name, price_text, deal_price, 
                original_price, unit_size, deal_tag, image_url, 
                valid_start_date, valid_end_date, category
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_data.get('store'),
            product_data.get('week'),
            product_data.get('year'),
            product_data.get('product_name'),
            product_data.get('price_text'),
            product_data.get('deal_price'),
            product_data.get('original_price'),
            product_data.get('unit_size'),
            product_data.get('deal_tag'),
            product_data.get('image_url'),
            product_data.get('valid_start_date'),
            product_data.get('valid_end_date'),
            product_data.get('category')
        ))
        conn.commit()
    except Exception as e:
        print(f"Error adding web product to DB: {e}")
    finally:
        conn.close()

def get_web_products(store=None, week=None, year=None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM web_products WHERE 1=1"
    params = []
    
    if store:
        query += " AND store = ?"
        params.append(store)
    if week:
        query += " AND week = ?"
        params.append(week)
    if year:
        query += " AND year = ?"
        params.append(year)
        
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]
