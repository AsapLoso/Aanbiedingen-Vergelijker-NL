import os
import sys

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.engine import engine

def test_extraction():
    test_text = "Heineken bier krat 24x0.3L van 18.99 voor 12.99"
    
    print(f"--- Testing LLM Extraction ---")
    print(f"Input: {test_text}")
    
    try:
        # Load the model (this will only happen if the .gguf file exists)
        deal = engine.extract_deal(test_text)
        
        print("\n✅ Extraction Success!")
        print(f"Brand: {deal.product.brand}")
        print(f"Name: {deal.product.name}")
        print(f"Unit: {deal.product.unit}")
        print(f"Price: {deal.price.current_price}")
        
    except FileNotFoundError:
        print("\n❌ Error: The model download is not yet complete or the file path is incorrect.")
        print(f"Looking for: {os.path.abspath(engine.model_path)}")
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    if not os.path.exists(engine.model_path):
        print(f"⚠️ Model file not found at {engine.model_path}")
        print("Please wait for the download to finish before running this test.")
    else:
        test_extraction()
