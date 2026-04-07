import sqlite3
import re
from collections import defaultdict

conn = sqlite3.connect('C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/deals.db')
cursor = conn.cursor()
cursor.execute('SELECT store, product_name FROM deals WHERE store != "Jumbo"')
deals = cursor.fetchall()
conn.close()

clusters = defaultdict(list)
for store, name in deals:
    # Get first two words
    words = [w for w in re.split(r'\W+', name) if w]
    key = " ".join(words[:2]).lower()
    clusters[key].append(name)

print(f"Total Non-Jumbo Deals: {len(deals)}")
print(f"Total 2-Word Clusters: {len(clusters)}")

# Print top clusters
sorted_clusters = sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True)
for key, items in sorted_clusters[:10]:
    print(f"  {key}: {len(items)} items -> {items[0][:40]}")
