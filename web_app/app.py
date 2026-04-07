import os
import sys
from flask import Flask, render_template, jsonify, request
import sqlite3

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from scraper.database import DealDatabase

app = Flask(__name__)
db_path = os.path.join(project_root, "data", "deals.db")

def get_db():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/grid")
def get_grid():
    """Returns pivoted deal data grouped by category and generic name."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Fetch only enriched deals with a category
    # We want the most recent deal per product/store combination
    cursor.execute("""
        SELECT *, MAX(extracted_at) as latest 
        FROM deals 
        WHERE category IS NOT NULL 
        GROUP BY generic_name, store
        ORDER BY category, generic_name
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Pivot: { Category: { GenericName: { Store: DealObj } } }
    grid = {}
    stores = ["Albert Heijn", "Aldi", "Dirk", "Jumbo", "Hoogvliet"]

    for row in rows:
        cat = row["category"] or "Overig"
        name = row["generic_name"] or row["product_name"]
        store = row["store"]

        if cat not in grid:
            grid[cat] = {}
        
        if name not in grid[cat]:
            grid[cat][name] = {s: None for s in stores}
            # Also store some metadata for the row
            grid[cat][name]["_metadata"] = {
                "variant": row["variant"]
            }
        
        grid[cat][name][store] = {
            "id": row["id"],
            "price": row["price"],
            "deal_tag": row["deal_tag"],
            "unit_size": row["package_amount"] or row["unit_size"],
            "image_url": row["image_url"],
            "raw_html": row["raw_html"]
        }

    return jsonify({"grid": grid, "stores": stores})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
