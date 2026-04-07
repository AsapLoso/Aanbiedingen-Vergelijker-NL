"""
run_pipeline.py — End-to-End Grocery Scraping Pipeline

1. Captures snapshots for all 5 stores (current + next week).
2. Parses deals with store-specific logic.
3. Stores all standardized deals into a local SQLite database.
"""

import os
import sys
import argparse
from datetime import datetime

# Add root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.web_scraper import SnapshotManager, STORES
from scraper.html_parser import DealParser
from scraper.database import DealDatabase

def run_pipeline(stores=None, headless=True, skip_future=False):
    """Run the full scrape-parse-store pipeline."""
    if stores and "all" in stores:
        target_stores = list(STORES.keys())
    else:
        target_stores = stores if stores else list(STORES.keys())
    
    # Initialize components
    sm = SnapshotManager(headless=headless)
    parser = DealParser()
    db = DealDatabase()
    
    print("="*60)
    print(f"🚀 RECIPES PIPELINE START: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    total_extracted = 0

    for store_key in target_stores:
        print(f"\n🏪 STORE: {STORES[store_key]['name'].upper()}")
        
        # We clear the store first to avoid stale data (optional, depends on policy)
        # db.clear_store(STORES[store_key]['name'])

        periods = ["current"]
        if not skip_future:
            periods.append("next")

        for period in periods:
            # 1. Capture
            filepath = sm.capture(store_key, period=period)
            if not filepath:
                continue

            # 2. Parse
            deals = parser.parse(filepath)
            if not deals:
                print(f"   ⚠️ No deals found for {store_key} ({period}).")
                continue

            # 3. Store
            count = db.insert_deals(deals)
            total_extracted += count
            print(f"   📥 Stored {count}/{len(deals)} deals in database.")

    print("\n" + "="*60)
    print(f"✅ PIPELINE FINISHED. Total deals processed: {total_extracted}")
    print("="*60)

if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("stores", nargs="*", help="Specific stores to run (optional)")
    argparser.add_argument("--headful", action="store_true", help="Run with visible browser")
    argparser.add_argument("--no-future", action="store_true", help="Skip the 'next week' scrape")
    
    args = argparser.parse_args()
    
    run_pipeline(
        stores=args.stores if args.stores else None,
        headless=not args.headful,
        skip_future=args.no_future
    )
