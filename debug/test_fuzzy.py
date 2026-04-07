import sqlite3
import re
from rapidfuzz import fuzz

conn = sqlite3.connect('C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/deals.db')
cursor = conn.cursor()
cursor.execute('SELECT store, product_name FROM deals WHERE store != "Jumbo"')
deals = cursor.fetchall()
conn.close()

clusters = []
for store, name in deals:
    placed = False
    for group_key, items in clusters:
        # Check similarity with the first item in the cluster
        if fuzz.ratio(name.lower(), group_key.lower()) > 75:
            items.append(name)
            placed = True
            break
    if not placed:
        clusters.append((name, [name]))

print(f"Total Non-Jumbo Deals: {len(deals)}")
print(f"Total Fuzzy Clusters: {len(clusters)}")

