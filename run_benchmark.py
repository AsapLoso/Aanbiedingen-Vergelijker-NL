import time
from llama_cpp import Llama

model_path = r"C:\Users\Deuts\OneDrive - Delft University of Technology\Misc\Gemini\Boodschappen\LLM\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
print("Loading model...")
llm = Llama(model_path=model_path, n_ctx=2048, n_threads=4, verbose=False)

def test_batch(size):
    # System prompt simulates the real instruction overhead
    sys = "You are a grocery extractor. Output JSON. " * 20
    
    # Build user prompt
    items = []
    for i in range(1, size+1):
        items.append(f"{i}. Apple {1.99 + i}")
    user = "Parse these:\n" + "\n".join(items)
    
    start = time.time()
    res = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": sys},
            {"role": "user", "content": user}
        ],
        max_tokens=1000
    )
    end = time.time()
    
    total_time = end - start
    print(f"Batch Size {size:>2} | Total Time: {total_time:>5.1f}s | Per Item: {total_time/size:>5.1f}s")

print("\n--- BENCHMARK ---")
for s in [1, 3, 5, 10, 15, 20]:
    test_batch(s)
