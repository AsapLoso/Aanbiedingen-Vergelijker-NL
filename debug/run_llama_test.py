import sys
import json
from llama_cpp import Llama
from pydantic import BaseModel, Field

class DealExtraction(BaseModel):
    generic_name: str
    price: float

class DealBatch(BaseModel):
    deals: list[DealExtraction]

print("Loading Llama...")
llm = Llama(model_path="C:/Users/Deuts/OneDrive - Delft University of Technology/Misc/Gemini/Boodschappen/LLM/Llama-3.2-3B-Instruct-Q4_K_M.gguf", n_ctx=2048, verbose=False)

schema = DealBatch.model_json_schema()

print("Running test batch...")
result = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "Extract data."},
        {"role": "user", "content": "1. Apple 1.99\n2. Banana 2.99"}
    ],
    max_tokens=500,
    response_format={"type": "json_object", "schema": schema}
)
print("Finished!")
print(result["choices"][0]["message"]["content"])
