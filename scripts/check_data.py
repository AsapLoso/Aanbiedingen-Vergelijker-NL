import os
import sys
from datetime import datetime

# Add project root to sys.path
import os
import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
from scraper.database import DealDatabase

def check_data():
    db = DealDatabase()
    stats = db.get_deal_stats()
    
    print("="*60)
    print(f"📊 DATABASE SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*60)
    
    total = 0
    for store, info in stats.items():
        print(f"🏪 {store.upper():15}: {info['count']:>5} deals | Period: {info['start']} to {info['end']}")
        total += info['count']
        
    print("-" * 60)
    print(f"📈 TOTAL DEALS: {total}")
    print("="*60)
    
    print("\n🎁 RECENT DEALS (Last 10):")
    recent = db.get_recent_deals(10)
    for d in recent:
        print(f"- [{d['store']}] {d['product_name']:40} | {d['price']:>6.2f} | {d['deal_tag']}")

if __name__ == "__main__":
    check_data()
