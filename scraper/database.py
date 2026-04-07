"""
database.py — SQLite Storage Manager for Grocery Deals

Provides a clean interface for:
- Initializing the database and 'deals' table.
- Inserting/updating deals.
- Cleaning up stale data (e.g. per-store).
"""

import sqlite3
import os
import datetime


class DealDatabase:
    """Manager for the local SQLite deals database."""

    def __init__(self, db_path=None):
        if db_path is None:
            # Default to data/deals.db relative to this file
            root = os.path.dirname(os.path.dirname(__file__))
            data_dir = os.path.join(root, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "deals.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Create a new SQLite connection."""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize the schema if not already present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    store TEXT NOT NULL,
                    product_name TEXT NOT NULL,
                    price REAL,
                    original_price REAL,
                    deal_tag TEXT,
                    unit_size TEXT,
                    image_url TEXT,
                    date_start TEXT,
                    date_end TEXT,
                    -- New structured fields for LLM enrichment (Refined Model Phase 5)
                    brand TEXT,
                    generic_name TEXT,
                    variant TEXT,
                    category TEXT,
                    package_amount TEXT,
                    items_in_cart INTEGER,
                    paid_equivalent REAL,
                    raw_html TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    -- Prevent duplicates of the same deal for the same period
                    UNIQUE(store, product_name, price, date_start, date_end)
                )
            """)
            conn.commit()
        self._migrate_db()

    def _migrate_db(self):
        """Add missing columns to existing database if needed."""
        new_cols = {
            "brand": "TEXT",
            "generic_name": "TEXT",
            "variant": "TEXT",
            "category": "TEXT",
            "package_amount": "TEXT",
            "items_in_cart": "INTEGER",
            "paid_equivalent": "REAL",
            "raw_html": "TEXT"
        }
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Get existing columns
            cursor.execute("PRAGMA table_info(deals)")
            existing_cols = [row[1] for row in cursor.fetchall()]
            
            for col, col_type in new_cols.items():
                if col not in existing_cols:
                    print(f"✨ Migrating: Adding column '{col}' to 'deals' table...")
                    cursor.execute(f"ALTER TABLE deals ADD COLUMN {col} {col_type}")
            conn.commit()

    def insert_deals(self, deals_list):
        """Batch insert a list of deal dictionaries."""
        if not deals_list:
            return 0

        with self._get_connection() as conn:
            cursor = conn.cursor()
            count = 0
            for d in deals_list:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO deals (
                            store, product_name, price, original_price,
                            deal_tag, unit_size, image_url, date_start, date_end
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        d.get("store"),
                        d.get("product_name"),
                        d.get("price"),
                        d.get("original_price"),
                        d.get("deal_tag"),
                        d.get("unit_size"),
                        d.get("image_url"),
                        d.get("date_start"),
                        d.get("date_end")
                    ))
                    count += 1
                except sqlite3.Error as e:
                    print(f"⚠️ Database error for {d.get('product_name')}: {e}")
            
            conn.commit()
            return count

    def clear_store(self, store_name):
        """Clear all deals for a specific store."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM deals WHERE store = ?", (store_name,))
            conn.commit()

    def get_all_deals(self):
        """Fetch all current deals in the database."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM deals ORDER BY store, product_name")
            return [dict(row) for row in cursor.fetchall()]

    def get_deal_stats(self):
        """Return a dictionary of deal counts per store and date range."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT store, COUNT(*), MIN(date_start), MAX(date_end) 
                FROM deals 
                GROUP BY store
            """)
            rows = cursor.fetchall()
            return {row[0]: {"count": row[1], "start": row[2], "end": row[3]} for row in rows}

    def get_recent_deals(self, limit=10):
        """Fetch the most recently extracted deals."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM deals ORDER BY extracted_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def clear_past_deals(self):
        """Delete deals where the end date is in the past."""
        today = datetime.date.today().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM deals WHERE date_end < ?", (today,))
            conn.commit()
            return cursor.rowcount

    def get_raw_deals(self, limit=None):
        """Fetch deals that haven't been enriched yet (brand is NULL)."""
        query = "SELECT * FROM deals WHERE brand IS NULL"
        params = []
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_enriched_deal(self, deal_id, data):
        """Update a deal with structured info from the LLM."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE deals SET 
                    brand = ?, 
                    generic_name = ?, 
                    variant = ?,
                    category = ?, 
                    package_amount = ?, 
                    items_in_cart = ?, 
                    paid_equivalent = ?
                WHERE id = ?
            """, (
                data.get("brand"),
                data.get("generic_name"),
                data.get("variant"),
                data.get("category"),
                data.get("package_amount"),
                data.get("items_in_cart"),
                data.get("paid_equivalent"),
                deal_id
            ))
            conn.commit()

    def toggle_selection(self, deal_id, is_selected):
        """Toggle the selection flag for a deal (used by UI for solver prep)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE deals SET is_selected = ? WHERE id = ?", (1 if is_selected else 0, deal_id))
            conn.commit()

    def save_raw_deal(self, deal_dict):
        """Save/Insert a raw deal, including raw_html if present."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO deals (
                        store, product_name, price, original_price, deal_tag, 
                        unit_size, image_url, raw_price_text, date_start, date_end, raw_html
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    deal_dict["store"], deal_dict["product_name"], deal_dict["price"],
                    deal_dict["original_price"], deal_dict["deal_tag"], deal_dict["unit_size"],
                    deal_dict["image_url"], deal_dict["raw_price_text"], 
                    deal_dict["date_start"], deal_dict["date_end"], deal_dict.get("raw_html")
                ))
                conn.commit()
            except sqlite3.Error as e:
                print(f"Error inserting deal: {e}")


if __name__ == "__main__":
    # Quick test
    db = DealDatabase()
    print(f"✅ Database initialized at: {db.db_path}")
