import os
import sys
import json

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from LLM.engine import start_engine, run_inference, stop_engine
from LLM.models import DealExtraction, GENERIC_EXTRACTION_PROMPT

def test_single_extraction():
    # Load categories just like the real script
    categories_path = os.path.join(project_root, "LLM", "categories.txt")
    with open(categories_path, "r", encoding="utf-8") as f:
        valid_categories = f.read().strip()

    test_deals = [
        {"name": "Heineken pilsener krat 24x0.3L", "tag": "1+1 gratis", "price": 18.99},
        {"name": "Zalmfilet op de huid", "tag": "2de halve prijs", "price": 12.00},
        {"name": "Robijn wasmiddel vloeibaar", "tag": "2+3 gratis", "price": 25.00},
        {"name": "Rundergehakt 500g", "tag": "Nu voor 4.99", "price": 4.99}
    ]

    try:
        start_engine()
        
        for deal in test_deals:
            print(f"\n🧪 Testing Deal: {deal['name']} | {deal['tag']}")
            
            user_prompt = f"""
Analyze the following grocery deal and extract the data as a JSON object.
Valid categories to choose from:
{valid_categories}

Product Name: {deal['name']}
Deal Tag: {deal['tag']}
Price: {deal['price']}
"""
            
            result = run_inference(
                data=user_prompt, 
                response_model=DealExtraction, 
                prompt=GENERIC_EXTRACTION_PROMPT
            )
            
            print("✅ Result:")
            print(json.dumps(result, indent=2))
            
    finally:
        stop_engine()

if __name__ == "__main__":
    test_single_extraction()
