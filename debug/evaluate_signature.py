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
    # Group by exact promotion signature
    key = f"{store}_{price}_{deal_tag}_{unit_size}"
    clusters[key].append(name)

print(f"Total Non-Jumbo Deals: {len(deals)}")
print(f"Total Signature Clusters: {len(clusters)}")

