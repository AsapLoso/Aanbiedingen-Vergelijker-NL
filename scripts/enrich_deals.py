import os
import sys
import argparse
import json
from tqdm import tqdm

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from scraper.database import DealDatabase
from LLM.engine import start_engine, run_inference, stop_engine
from LLM.models import DealExtraction, GENERIC_EXTRACTION_PROMPT

def enrich_deals(limit=None, batch_size=10):
    """
    Fetch un-enriched deals from the DB and process them through the LLM.
    Uses the Mistral-7B engine with the refined DealExtraction model.
    """
    db = DealDatabase()
    
    # 1. Load categories
    categories_path = os.path.join(project_root, "LLM", "categories.txt")
    if not os.path.exists(categories_path):
        print(f"❌ Could not find categories.txt at {categories_path}")
        return
        
    with open(categories_path, "r", encoding="utf-8") as f:
        valid_categories = f.read().strip()

    # 2. Fetch raw deals (brand IS NULL)
    raw_deals = db.get_raw_deals(limit=limit)
    if not raw_deals:
        print("✅ No new deals to enrich. Database is up to date!")
        return

    print(f"🧠 Found {len(raw_deals)} deals requiring AI enrichment.")
    
    # 3. Start the LLM engine
    try:
        start_engine()
    except Exception as e:
        print(f"❌ Could not start LLM engine: {e}")
        return

    # 4. Process in batches
    enriched_count = 0
    try:
        for i in tqdm(range(0, len(raw_deals), batch_size), desc="Enriching Batches"):
            batch = raw_deals[i : i + batch_size]
            
            for deal in batch:
                try:
                    # Construct user prompt with supplemental info
                    scraped_hint = f" (Scraped Size: {deal['unit_size']})" if deal['unit_size'] else ""
                    
                    user_prompt = f"""
Analyze the following grocery deal and extract the data as a JSON object.
Valid categories to choose from:
{valid_categories}

Product Name: {deal['product_name']}{scraped_hint}
Deal Tag: {deal['deal_tag'] or 'Geen actie'}
Price: {deal['price']}
"""
                    
                    # Run inference
                    # User's engine.py signature: (data, response_model, prompt)
                    # result is a dictionary
                    result = run_inference(
                        data=user_prompt, 
                        response_model=DealExtraction, 
                        prompt=GENERIC_EXTRACTION_PROMPT
                    )
                    
                    # Supplement-Only Logic: 
                    # If we had a scraped size, and the AI output is generic ('1 stuk' or empty),
                    # we prioritize the scraper's original find.
                    llm_amount = result.get("package_amount")
                    if deal['unit_size'] and (not llm_amount or "stuk" in llm_amount.lower()):
                        result["package_amount"] = deal['unit_size']
                    
                    # Update database with specific fields from the new model
                    db.update_enriched_deal(deal['id'], result)
                    enriched_count += 1
                    
                except Exception as e:
                    print(f"   ⚠️ Error enriching deal ID {deal['id']} ({deal['product_name']}): {e}")
                    continue
                    
    finally:
        # 5. Always stop the engine to free RAM
        stop_engine()

    print(f"\n✨ Enrichment finished! Successfully updated {enriched_count} deals.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enrich raw grocery deals using a local LLM.")
    parser.add_argument("--limit", type=int, help="Limit the number of deals to process (e.g. 5 for testing)")
    parser.add_argument("--batch", type=int, default=10, help="Batch size for tqdm display")
    
    args = parser.parse_args()
    enrich_deals(limit=args.limit, batch_size=args.batch)
