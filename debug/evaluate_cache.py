import sqlite3
import urllib.parse
from fuzzywuzzy import fuzz

conn = sqlite3.connect('C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/deals.db')
cursor = conn.cursor()
# Count unique product names
cursor.execute('SELECT COUNT(DISTINCT product_name) FROM deals')
unique = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(product_name) FROM deals')
total = cursor.fetchone()[0]

print(f"Total rows: {total}")
print(f"Unique exact product names: {unique}")

