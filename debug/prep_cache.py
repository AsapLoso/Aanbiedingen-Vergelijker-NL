import sqlite3
import json
import os

db_path = 'C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/deals.db'
cache_path = 'C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/llm_cache.json'

cache = {}
if os.path.exists(cache_path):
    with open(cache_path, 'r', encoding='utf-8') as f:
        cache = json.load(f)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all enriched deals
cursor.execute("SELECT store, product_name, generic_name, category, package_amount, items_in_cart, paid_equivalent FROM deals WHERE category IS NOT NULL")
enriched_rows = cursor.fetchall()

added = 0
for row in enriched_rows:
    p_name = row['product_name']
    store = row['store']
    
    # We used f"{store}_{p_name}" in enrich_deals.py
    cache_key = f"{store}_{p_name}"
    
    if cache_key not in cache:
        # Reconstruct the Mistral dictionary format
        # package_amount format: "500 g" -> {value: "500", unit: "g"}
        size_obj = {}
        if row['package_amount']:
            parts = row['package_amount'].split(' ')
            if len(parts) >= 2:
                size_obj = {"value": parts[0], "unit": " ".join(parts[1:])}
            else:
                size_obj = {"value": parts[0], "unit": ""}
                
        cache[cache_key] = {
            "generic_name": row['generic_name'],
            "category": row['category'],
            "size": size_obj,
            "paid_equivalent": row['paid_equivalent']
        }
        added += 1

conn.close()

with open(cache_path, 'w', encoding='utf-8') as f:
    json.dump(cache, f, indent=2)

print(f"Successfully backfilled {added} items from existing database into llm_cache.json")
