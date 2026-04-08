import time
from llama_cpp import Llama

model_path = r"C:\Users\Deuts\OneDrive - Delft University of Technology\Misc\Gemini\Boodschappen\LLM\Llama-3.2-3B-Instruct-Q4_K_M.gguf"
print("Loading model...")
llm = Llama(model_path=model_path, n_ctx=2048, n_threads=4, verbose=True)

prompt = "Analyze these grocery items:\n1. Apple 1.99\n2. Banana 2.99\nOutput JSON."

start = time.time()
print("Generating...")
res = llm.create_chat_completion(
    messages=[{"role": "user", "content": prompt}],
    max_tokens=500
)
end = time.time()

time_taken = end - start
tokens = res['usage']['completion_tokens']
print(f"Time: {time_taken:.2f}s")
print(f"Tokens Gen: {tokens}")
print(f"Speed: {tokens / time_taken:.2f} tokens/s")
