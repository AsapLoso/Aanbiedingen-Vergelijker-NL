import sqlite3
import os
import json
import sys
import math

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import DB_PATH

BATCH_SIZE = 300

def export_for_ai():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get unique products
    c.execute("SELECT DISTINCT product_name FROM products")
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("No products found.")
        return

    # Just a list of names
    products = [row[0] for row in rows if row[0]]
    total_products = len(products)
    print(f"Found {total_products} unique products.")

    base_prompt = """
Ik heb een lijst met supermarktproducten. Categoriseer ze en geef een strikt gestandaardiseerde, generieke naam.

BELANGRIJK: DOEL VAN DE STANDAARDISATIE Het doel is om prijzen te vergelijken. Variaties moeten worden samengevoegd.
    "Appels Elstar", "Appels Pink Lady" en "Handappels" moeten allemaal worden: "Appels".
    "Avocado" en "Avocado's" moeten allemaal worden: "Avocado" (kies één vorm).
    "Unox Rookworst" en "Hema Rookworst" moeten allemaal worden: "Rookworst".

REGELS VOOR STANDAARDISATIE:
    Verwijder alle merknamen (bijv. "Unox", "Lay's", "Jumbo").
    Verwijder alle variëteiten/smaken (bijv. "Elstar", "Paprika", "Halfvolle", "Pink Lady"). Houd alleen het basisproduct over.
    Verwijder verpakkingen/hoeveelheden (bijv. "zak", "net", "500g", "6-pack").
    Gebruik ALTIJD meervoud waar logisch (bijv. altijd "Appels", nooit "Appel").
    Bij twijfel of mix-producten ("Appels of Peren"): Kies het eerste of meest dominante product (bijv. "Appels").
    Nonsense: Als het geen product is (datum, afmeting), zet category op "Nonsense".

Output ONLY valid JSON: [ {"original_name": "...", "standardized_name": "...", "category": "..."} ]

Categories:
    AGF
    Vlees, Vis & Vega
    Zuivel & Eieren
    Brood & Ontbijt
    Voorraadkast
    Snoep & Snacks
    Drinken
    Alcohol
    Huishouden & Verzorging
    Diepvries
    Overige
    Nonsense

Product List:
"""
    
    num_batches = math.ceil(total_products / BATCH_SIZE)
    print(f"Splitting into {num_batches} files (approx {BATCH_SIZE} items each).")
    
    for i in range(num_batches):
        batch_products = products[i*BATCH_SIZE : (i+1)*BATCH_SIZE]
        output_file = os.path.join(os.path.dirname(__file__), f'prompt_{i+1}.txt')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(base_prompt + json.dumps(batch_products, indent=2))
            
        print(f"  -> Created: {output_file}")

    print("\nINSTRUCTIONS:")
    print("1. Open each 'scripts/prompt_X.txt' file.")
    print("2. Copy content to your AI.")
    print("3. Paste the AI's JSON response BACK into the SAME file (Overwrite it).")
    print("4. Repeat for all files.")
    print("5. Run scripts/import_ai_data.py")

if __name__ == "__main__":
    export_for_ai()
