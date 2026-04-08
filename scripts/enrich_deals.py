import os
import sys
import argparse
import json
import sqlite3
from tqdm import tqdm

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from scraper.database import DealDatabase
from LLM.engine import start_engine, run_inference, stop_engine
from LLM.models import DutchGroceryModel, DUTCH_GROCERY_PROMPT, DutchGroceryBatch, DUTCH_GROCERY_BATCH_TASK

def enrich_deals(limit=None, batch_size=None):
    """
    Fetch un-enriched deals from the DB and process them through the LLM.
    Uses Clustering to reduce LLM calls and Batching for parallel inference speed.
    """
    # 0. Auto-Load Hardware Profile
    if batch_size is None:
        profile_path = os.path.join(project_root, "data", "hardware_profile.json")
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                    batch_size = profile.get("optimal_batch_size", 5)
                    print(f"⚙️ Loaded Hardware Profile: Auto-calibrated batch size to {batch_size}")
            except:
                batch_size = 5
        else:
            batch_size = 5 # Default safe dual-core baseline
            print(f"⚠️ No hardware profile found. Using safe default batch size: {batch_size}")
            print(f"   (Run 'python scripts/benchmark_cpu.py' to optimize this for your machine!)")

    db = DealDatabase()
    
    # 1. Fetch raw deals (brand IS NULL means they haven't been enriched)
    all_raw_deals = db.get_raw_deals()
    if not all_raw_deals:
        print("✅ No new deals to enrich. Database is up to date!")
        return

    print(f"🧠 Found {len(all_raw_deals)} deals requiring AI enrichment.")

    # 2. Semantic Clustering (Group identical products to hit LLM only once)
    # Most stores (especially Jumbo) have many duplicates across pages.
    clusters = {}
    for deal in all_raw_deals:
        # Create a unique key based on the product identity
        # (store, name, and deal_tag are Usually enough)
        key = (deal['store'], deal['product_name'], deal['deal_tag'])
        if key not in clusters:
            clusters[key] = []
        clusters[key].append(deal)

    unique_keys = list(clusters.keys())
    print(f"🧩 Clustered {len(all_raw_deals)} items into {len(unique_keys)} distinct AI inference tasks.")

    if limit:
        unique_keys = unique_keys[:limit]
        print(f"⚠️ Limit applied: Only processing {limit} clusters.")

    # 3. Cache Management
    # We use data/llm_cache.json to persist results across runs
    cache_path = os.path.join(project_root, "data", "llm_cache.json")
    llm_cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r", encoding="utf-8") as f:
            try:
                llm_cache = json.load(f)
            except:
                llm_cache = {}

    # Drain cache first
    uncached_keys = []
    cached_count = 0
    for key in unique_keys:
        cache_key = str(key) # JSON keys must be strings
        if cache_key in llm_cache:
            result = llm_cache[cache_key]
            # Update all deals in this cluster
            for deal in clusters[key]:
                db.update_enriched_deal(deal['id'], result)
            cached_count += 1
        else:
            uncached_keys.append(key)

    if cached_count > 0:
        print(f"🗃️ Loaded {cached_count} items from persistent LLM cache.")

    if not uncached_keys:
        print("✅ All items were found in cache. Done!")
        return

    # 4. Start the LLM engine for uncached items
    try:
        start_engine()
    except Exception as e:
        print(f"❌ Could not start LLM engine: {e}")
        return

    # 5. Batch Inference (Big Brain Move: 10 at a time)
    print(f"🔥 Sending {len(uncached_keys)} clusters to AI in batches of {batch_size}...")
    
    try:
        for i in tqdm(range(0, len(uncached_keys), batch_size), desc="Batch Inference"):
            batch_keys = uncached_keys[i : i + batch_size]
            
            # Construct a numbered list for the batch prompt
            batch_data = []
            for idx, key in enumerate(batch_keys, 1):
                store, name, tag = key
                batch_data.append(f"{idx}. [{store}] {name} (Tag: {tag or 'None'})")
            
            user_prompt = "Process these deals in a batch:\n" + "\n".join(batch_data)
            
            try:
                # Run inference using the DutchGroceryBatch model
                # This returns a dict with a "deals" list
                # Use max_tokens=4096 explicitly to handle large batches
                result_batch = run_inference(
                    data=user_prompt, 
                    response_model=DutchGroceryBatch, 
                    prompt=DUTCH_GROCERY_PROMPT,
                    max_tokens=4096
                )
                
                extracted_list = result_batch.get("deals", []) if isinstance(result_batch, dict) else []
                
                # Zip and Save
                for j, key in enumerate(batch_keys):
                    if j < len(extracted_list):
                        # Pydantic model dump
                        result = extracted_list[j]
                        
                        # Prepare DB update dict
                        # We need to map the DutchGroceryModel fields to the DB columns
                        # package_amount = size.value + size.unit
                        size = result.get("size", {})
                        db_payload = {
                            "brand": "Generic", # Simplified for now
                            "generic_name": result.get("generic_name"),
                            "variant": "",
                            "category": result.get("category"),
                            "package_amount": f"{size.get('value')} {size.get('unit')}" if size else "",
                            "items_in_cart": int(result.get("paid_equivalent", 1.0)), # approximation
                            "paid_equivalent": result.get("paid_equivalent", 1.0)
                        }
                        
                        # Update DB for all items in this cluster
                        for deal in clusters[key]:
                            db.update_enriched_deal(deal['id'], db_payload)
                        
                        # Save to cache
                        llm_cache[str(key)] = db_payload
                
                # Periodically save cache to disk
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(llm_cache, f, indent=4)
                    
            except Exception as e:
                print(f"   ⚠️ Batch error: {e}")
                continue
                
    finally:
        stop_engine()

    print(f"\n✨ Enrichment finished! Successfully processed all items.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich raw grocery deals using a local LLM.")
    parser.add_argument("--limit", type=int, help="Limit the number of clusters to process")
    parser.add_argument("--batch", type=int, default=None, help="Batch size for LLM inference (Overrides Hardware Profile)")
    
    args = parser.parse_args()
    enrich_deals(limit=args.limit, batch_size=args.batch)
