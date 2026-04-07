# LLM Framework Instructions

This directory contains the localized LLM engine used for structured grocery data extraction.

## Core Functions

The framework is exposed as three main functions in `llm/engine.py`.

### 1. `start_engine()`
Loads the 6GB+ GGUF model into system RAM.
- **When to use**: Once at the beginning of your script.
- **Note**: This takes several seconds and allocates ~7-8GB of RAM.

```python
from llm.engine import start_engine
start_engine()
```

### 2. `run_inference(data, response_model, prompt, retries=3)`
Sends raw text to the model and returns a dictionary.
- **Parameters**:
    - `data`: The raw text snippet or HTML from a product card.
    - `response_model`: The Pydantic class to map the data into (e.g. `DutchGroceryModel`).
    - `prompt`: The specific instructions for how to parse the data (e.g. `DUTCH_GROCERY_PROMPT`).
- **Features**:
    - **Automatic Templating**: The engine uses the Pydantic field `descriptions` from your model to guide the LLM.
    - **Retries**: Automatically retries if JSON parsing fails.
- **Returns**: A Python dictionary matching the keys in your `response_model`.

### 3. `stop_engine()`
Shuts down the engine and explicitly frees the RAM.
- **When to use**: Always call this after your processing run is finished.

```python
from llm.engine import stop_engine
stop_engine()
```

---

## Expert Dutch Supermarket Extraction

For specialized Dutch grocery deals, use the pre-defined **DutchGroceryModel** and its expert analyst prompt.

**Definition (`llm/models.py`)**:
*   **Brand**: Product brand.
*   **Name**: Main product name.
*   **Price**: Listed price.
*   **Paid Equivalent**: Calculated cost per standard unit or actual amount paid per pack.
*   **Package Amount**: Size or weight (e.g., 500g, 1L).
*   **Category**: Must be one of 15 valid Dutch categories (see `categories.txt`).

**Usage**:
```python
from llm import engine
from llm.models import DUTCH_GROCERY_TASK # Pair (DutchGroceryModel, DUTCH_GROCERY_PROMPT)

# Unpack the tuple directly into run_inference
result = engine.run_inference(raw_text, *DUTCH_GROCERY_TASK)
print(result["category"])
```

## Best Practices

1. **Warm Load**: Call `start_engine()` once at the top of your script. Do **not** call it inside a loop.
2. **Field Descriptions**: Be descriptive in your Pydantic `Field(..., description="...")` tags. The engine uses these descriptions as part of its system instructions.
3. **Selective Use**: AI extraction is slower than regex. Use standard BeautifulSoup/Regex first, and only call `run_inference` if data is missing or messy.
