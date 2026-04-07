import os
import sys
import glob

# Add project root to sys.path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)

from scraper.html_parser import DealParser
from scraper.database import DealDatabase

def reparse():
    dp = DealParser()
    db = DealDatabase()
    
    # Target today's files
    raw_dir = os.path.join(root, "data", "raw")
    files = glob.glob(os.path.join(raw_dir, "*_2026-04-07.html"))
    # Also include jumbo directory for today
    jumbo_dirs = glob.glob(os.path.join(raw_dir, "jumbo_2026-04-07"))
    
    all_targets = files + jumbo_dirs
    print(f"🔄 Reparsing {len(all_targets)} targets...")

    for target in all_targets:
        print(f"   📄 Processing {os.path.basename(target)}...")
        deals = dp.parse(target)
        if deals:
            count = db.insert_deals(deals)
            print(f"   📥 Re-inserted {count}/{len(deals)} deals.")

if __name__ == "__main__":
    reparse()
