"""
test_extraction.py — End-to-end test of the scraping pipeline.

Captures a snapshot for a store, then parses it and prints the results.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper.web_scraper import SnapshotManager, STORES
from scraper.html_parser import DealParser


def clc():
    os.system("cls" if os.name == "nt" else "clear")


def test_store(store_key, headless=True):
    """Run the full pipeline for a single store."""
    print(f"\n{'='*60}")
    print(f"  TESTING: {STORES[store_key]['name']}")
    print(f"{'='*60}")

    # Step 1: Capture
    sm = SnapshotManager(headless=headless)
    filepath = sm.capture(store_key)

    if not filepath:
        print(f"\n❌ CAPTURE FAILED for {store_key}")
        return []

    # Step 2: Parse
    parser = DealParser()
    deals = parser.parse(filepath)

    # Step 3: Print results
    print(f"\n{'─'*60}")
    print(f"  RESULTS: {len(deals)} deals from {STORES[store_key]['name']}")
    print(f"{'─'*60}")

    if not deals:
        print("  (no deals extracted)")
        return deals

    print(f"  {'PRODUCT':<32} │ {'PRICE':>7} │ TAG")
    print(f"  {'─'*32}─┼─{'─'*7}─┼─{'─'*20}")

    for d in deals[:20]:
        name = d["product_name"]
        if len(name) > 30:
            name = name[:28] + ".."
        price = f"€{d['price']:.2f}" if d["price"] > 0 else "  -   "
        tag = d["deal_tag"] or "-"
        print(f"  {name:<32} │ {price:>7} │ {tag}")

    remaining = len(deals) - 20
    if remaining > 0:
        print(f"\n  ... and {remaining} more deals.")

    # Summary stats
    priced = [d for d in deals if d["price"] > 0]
    named = [d for d in deals if d["product_name"] != "Unknown"]
    print(f"\n  📊 Stats: {len(named)}/{len(deals)} named, "
          f"{len(priced)}/{len(deals)} with price")

    return deals


def main():
    clc()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║        BOODSCHAPPEN — Scraper Pipeline Test             ║")
    print("╚══════════════════════════════════════════════════════════╝")

    # Parse CLI args
    store_keys = sys.argv[1:] if len(sys.argv) > 1 else ["dirk"]

    if "all" in store_keys:
        store_keys = list(STORES.keys())

    all_deals = {}
    for key in store_keys:
        if key in STORES:
            all_deals[key] = test_store(key, headless=True)
        else:
            print(f"\n⚠️ Unknown store: {key}. Options: {list(STORES.keys())}")

    # Final summary
    print(f"\n{'═'*60}")
    print(f"  SUMMARY")
    print(f"{'═'*60}")
    for key, deals in all_deals.items():
        status = f"✅ {len(deals)} deals" if deals else "❌ failed"
        print(f"  {STORES[key]['name']:<20} {status}")
    print()


if __name__ == "__main__":
    main()
