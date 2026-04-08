import os
import sys
import time
import json
import argparse
from tqdm import tqdm

# Add project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from LLM.engine import start_engine, run_inference, stop_engine
from LLM.models import DutchGroceryBatch, DUTCH_GROCERY_PROMPT, VALID_CATEGORIES_STRING

def run_benchmark(max_batch_size=10):
    """
    Benchmarks CPU inference speed across different batch sizes to find the 'Sweet Spot'.
    This is critical because CPU inference suffers from quadratic scaling ($N^2$) 
    when contexts get too large.
    """
    print("=" * 60)
    print("🚀 CPU BATCHING BENCHMARK UTILITY")
    print("=" * 60)
    
    # Generate generic mock deals
    test_deals = [
        f"{i}. [AH] Jumbo Pindakaas 350g (Tag: Nu voor {3.99 + (i*0.10):.2f})" for i in range(1, max_batch_size + 1)
    ]
    
    batch_sizes = [1, 2, 3, 5, 10]
    batch_sizes = [s for s in batch_sizes if s <= max_batch_size]

    results = []

    try:
        # Load model into RAM once
        start_engine()
        
        print("\n🔥 Running Warmup (Absorbing cold-start KV cache allocation penalty)...")
        run_inference("Process: 1. Apple 1.99", DutchGroceryBatch, DUTCH_GROCERY_PROMPT, max_tokens=256, retries=1)
        
        for size in batch_sizes:
            print(f"\n🧪 Testing Batch Size: {size}")
            
            # Construct exact prompt format identical to the pipeline
            batch_data = test_deals[:size]
            user_prompt = "Process these deals in a batch:\n" + "\n".join(batch_data)
            
            # Start timer (includes prompt processing + generation)
            start_time = time.time()
            
            try:
                # We enforce max_tokens=4096 just like the real pipeline
                result_batch = run_inference(
                    data=user_prompt, 
                    response_model=DutchGroceryBatch, 
                    prompt=DUTCH_GROCERY_PROMPT,
                    max_tokens=4096,
                    retries=1 # Fail fast in benchmarking
                )
                
                success = True
                extracted = result_batch.get("deals", []) if isinstance(result_batch, dict) else []
                items_extracted = len(extracted)
            except Exception as e:
                success = False
                print(f"❌ Failed: {e}")
                items_extracted = 0
                
            end_time = time.time()
            total_time = end_time - start_time
            time_per_item = total_time / size if success else float('inf')
            
            results.append({
                "batch_size": size,
                "total_time": total_time,
                "time_per_item": time_per_item,
                "success": success,
                "items_returned": items_extracted
            })
            
            if success:
                print(f"✅ Success! Generated JSON array with {items_extracted} item(s)")
                print(f"⏱️  Total Time:   {total_time:>6.2f} seconds")
                print(f"⚡ Time/Item:    {time_per_item:>6.2f} seconds")

    finally:
        stop_engine()

    # Calculate optimal size
    print("\n" + "=" * 60)
    print("🏆 BENCHMARK RESULTS")
    print("=" * 60)
    
    valid_results = [r for r in results if r["success"]]
    if not valid_results:
        print("❌ All benchmarks failed. Ensure your model fits in RAM.")
        return
        
    optimal_size = min(valid_results, key=lambda x: x["time_per_item"])["batch_size"]
    
    # Save the calibration globally
    config_path = os.path.join(project_root, "data", "hardware_profile.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({"optimal_batch_size": optimal_size}, f, indent=4)
    
    print(f"{'Batch Size':<12} | {'Total Time':<12} | {'Time per Item':<15} | {'Status'}")
    print("-" * 60)
    for r in results:
        status = "✅" if r["success"] else "❌"
        tpi = f"{r['time_per_item']:.2f}s" if r["success"] else "N/A"
        is_opt = " ⭐ BEST (Saved to Hardware Profile)" if r["batch_size"] == optimal_size else ""
        print(f"{r['batch_size']:<12} | {r['total_time']:>6.2f}s      | {tpi:>10}      | {status}{is_opt}")
        
    print(f"\n💾 Hardware Profile saved to: {config_path}")
    print("\n💡 NOTE: This optimization only measures CPU compute scaling. GPU users (CUDA/Metal) will likely see linear improvement with much larger batches.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find optimal CPU batch size for LLM extraction.")
    parser.add_argument("--max", type=int, default=10, help="Maximum batch size to test")
    
    args = parser.parse_args()
    run_benchmark(max_batch_size=args.max)
