import os
import gc
import json
import time
from llama_cpp import Llama

# Default model path (using absolute path for stability)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_MODEL_PATH = os.path.join(_BASE_DIR, "LLM", "Mistral-7B-Instruct-v0.3-Q6_K.gguf")

# Global singleton storage
_LLM = None

def start_engine(model_path: str = DEFAULT_MODEL_PATH, n_ctx: int = 1024, n_threads: int = 4):
    """
    Initialize the LLM engine and load it into RAM.
    Does nothing if already started.
    """
    global _LLM
    
    if _LLM is not None:
        return

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file found: {model_path}")

    print(f"📦 Starting LLM engine (loading into RAM)...")
    
    _LLM = Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        verbose=False
    )
    print("✅ Engine started successfully.")

def stop_engine():
    """
    Shutdown the LLM engine and free up system RAM.
    """
    global _LLM
    
    if _LLM is None:
        return

    print("🔌 Shutting down LLM engine and freeing RAM...")
    _LLM = None
    
    # Force garbage collection to release the ~6GB
    gc.collect()
    print("✅ RAM cleared.")

def run_inference(data: str, response_model, prompt: str, max_tokens: int = 256, retries: int = 3):
    """
    Perform structured extraction from data.
    Returns a dictionary (parsed JSON) matching the model fields.
    
    Args:
        data:           The raw text or HTML to analyze.
        response_model: Pydantic model to define required fields.
        prompt:         Instructions for the LLM.
        max_tokens:     Limit for output generation.
        retries:        Number of attempts on JSON failure.
    """
    global _LLM
    
    if _LLM is None:
        raise RuntimeError("LLM engine not started. Call LLM.engine.start_engine() first.")

    # 1. Build the prompt template based on model fields
    # Extract field names and descriptions from the Pydantic model
    fields_info = response_model.model_fields
    field_instructions = "\n".join([f"- Return '{f}' as one of the keys in your response. "
                                   f"Description: {fields_info[f].description}" for f in fields_info])
    
    system_prompt = (
        "You are a professional data extraction assistant. "
        "Extract information from the provided data and return a valid JSON object. "
        "Follow these field instructions precisely:\n"
        f"{field_instructions}\n"
        "Respond ONLY with the JSON object, no preamble or explanation."
    )
    
    user_prompt = f"{prompt}\n---\nData: {data}"

    # 2. Schema for constrained generation
    schema = response_model.model_json_schema()

    # 3. Retry loop
    for attempt in range(retries):
        try:
            print(f"🤖 Inference attempt {attempt + 1}/{retries}...")
            
            result = _LLM.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0,  # Deterministic
                response_format={
                    "type": "json_object",
                    "schema": schema
                }
            )

            raw_json = result["choices"][0]["message"]["content"]
            parsed_dict = json.loads(raw_json)
            
            return parsed_dict

        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(1)  # Brief pause before retry
            else:
                raise RuntimeError(f"LLM extraction failed after {retries} attempts: {e}")

if __name__ == "__main__":
    # Test block for local execution
    from .models import DutchGroceryModel, DUTCH_GROCERY_PROMPT
    test_text = "Heineken bier krat 24x0.3L van 18.99 voor 12.99"
    try:
        start_engine()
        result = run_inference(test_text, DutchGroceryModel, DUTCH_GROCERY_PROMPT)
        print("\n✅ Extraction Success!")
        print(json.dumps(result, indent=2))
        stop_engine()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
