import os
from llama_cpp import Llama

model_path = r"C:\Users\Deuts\OneDrive - Delft University of Technology\Misc\Gemini\Boodschappen\LLM\gemma-4-E4B-it-Q6_K.gguf"

print(f"🔍 Testing model load: {model_path}")
if not os.path.exists(model_path):
    print("❌ File does not exist!")
    exit(1)
else:
    print(f"✅ File exists. Size: {os.path.getsize(model_path)} bytes")

try:
    print("🚀 Initializing Llama...")
    llm = Llama(model_path=model_path, verbose=True)
    print("✅ Success!")
except Exception as e:
    print(f"❌ Failed: {e}")
