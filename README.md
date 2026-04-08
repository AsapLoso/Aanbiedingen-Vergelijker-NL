# AI-Powered Grocery Deal Aggregator

An automated pipeline for scraping, processing, and analyzing weekly grocery deals from major Dutch supermarkets. This tool uses LLM-based extraction to structure data and provide a unified dashboard for price comparison and savings optimization.

## 🚀 Features

- **Automated Scraping**: Multi-supermarket support (AH, Aldi, Dirk, Jumbo, Hoogvliet) using Selenium and BeautifulSoup.
- **LLM Data Extraction**: Utilizes a local Gemma-4 model (via `llama-cpp-python` & `instructor`) to extract structured price, quantity, and category information from raw HTML/text.
- **Unified Database**: Stores all scraped deals in an optimized SQLite database for historical tracking.
- **Web Dashboard**: Interactive Flask-based interface to browse deals, filter by category, and compare prices across stores.
- **Pipeline Automation**: Single-script execution for the entire workflow (Scrape → AI Extract → Web App).

## 🛠️ Architecture

1.  **Scraper (`/scraper`)**: Handles supermarket-specific web interactions and raw data collection.
2.  **AI Engine (`/LLM`)**: Manages local inference using GGUF models to convert unstructured deal text into Pydantic models.
3.  **Solver (`/solver`)**: Optimization engine (Pulp) for grocery budget management (future).
4.  **Web App (`/web_app`)**: Frontend for visualizing deals and comparison data.
5.  **Data (`/data`)**: Persistent storage for SQLite databases and raw snapshots.

## 📋 Prerequisites

- **Python 3.10+** (Recommend using Conda or a virtual environment)
- **Local LLM**: Download a GGUF model (e.g., `gemma-4-E4B-it-Q6_K.gguf`) and place it in the `LLM/` directory.

## ⚙️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/grocery-aggregator.git
    cd grocery-aggregator
    ```

2.  **Create and activate environment**:
    ```bash
    conda create -n boodschappen python=3.10
    conda activate boodschappen
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Browser Drivers** (for Selenium/Scraping):
    Ensure you have Chromium/Chrome installed.

## 🚀 Usage

### 1. Run the Full Pipeline
Executes scraping and processing sequentially:
```bash
python scripts/run_pipeline.py
```

### 2. CPU Hardware Optimization (Benchmarking)
If you are running the LLM engine locally on a CPU, you MUST optimize the logical batch size for your specific hardware. Large batches on older CPUs suffer from quadratic calculation slowdowns ($N^2$).

Run the benchmark utility to find your "Hardware Sweet-Spot":
```bash
python scripts/benchmark_cpu.py --max 10
```
*Note: This optimization is strictly for **CPU inference**. If you process via a dedicated GPU (CUDA/Metal), larger batches will linearly improve throughput.*

### 3. Local LLM Framework (Power Users)
The project includes a localized LLM engine (`llama-cpp-python`) for structured data extraction.

**Initialization**:
```python
from llm.engine import start_engine
start_engine()
```

**Run Extraction** (Explicit model + prompt):
```python
from llm import engine
from llm.models import PRODUCT_DEALS

# Unpack the model-prompt tuple directly
result = engine.run_inference("Heineken 24x0.3L €12.99", *PRODUCT_DEALS)
print(result["brand"])
```

**Cleanup** (Frees ~6-8GB RAM):
```python
from llm.engine import stop_engine
stop_engine()
```

For more details, see [llm/instructions.md](file:///c:/Users/Deuts/OneDrive%20-%20Delft%20University%20of%20Technology/Misc/Gemini/Boodschappen/llm/instructions.md).

## 📂 Project Structure

```text
.
├── LLM/                # AI Inference & GGUF Models (Ignored by Git)
├── data/               # SQLite database and raw HTML files
├── scraper/            # Supermarket-specific scrapers
├── scripts/            # Pipeline management & utility scripts
├── solver/             # Price optimization logic
├── web_app/            # Flask server & HTML templates
├── requirements.txt    # Project dependencies
└── README.md           # This file!
```

## ⚠️ Important Note on Large Files
Large model files (GGUF) and local databases are excluded from Git to keep the repository lightweight. Please refer to the documentation or contact the maintainer to obtain the base model and data snapshots.

## 📜 License
MIT License / Private (As applicable)
