import sqlite3

db_path = 'C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/data/deals.db'

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT store, COUNT(*), COUNT(deal_group) FROM deals GROUP BY store')
    rows = cursor.fetchall()
    
    print(f"{'Store':<15} | {'Deals':<7} | {'Has Deal Group':<15}")
    print("-" * 45)
    for row in rows:
        print(f"{row[0]:<15} | {row[1]:<7} | {row[2]:<15}")
        
    conn.close()
except Exception as e:
    print(f"Error querying db: {e}")
