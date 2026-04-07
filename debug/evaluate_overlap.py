import sqlite3
import re
from collections import defaultdict

conn = sqlite3.connect('C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/deals.db')
cursor = conn.cursor()
cursor.execute('SELECT store, price, deal_tag, unit_size, product_name FROM deals WHERE store != "Jumbo"')
deals = cursor.fetchall()
conn.close()

clusters = defaultdict(list)
for store, price, deal_tag, unit_size, name in deals:
    key = f"{store}_{price}_{deal_tag}_{unit_size}"
    clusters[key].append(name)

sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
for key, items in sorted_clusters[:10]:
    print(f"{key}: {len(items)} items")
    print(f"  Sample: {items[:3]}")

