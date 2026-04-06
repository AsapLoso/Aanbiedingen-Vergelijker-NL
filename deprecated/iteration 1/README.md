# Iteration 1: Folder-based Approach (Legacy)

This directory contains the original implementation of the grocery scraper, which focused on processing local flyer files (PDFs and images).

## Overview
The workflow involved:
1.  **Scraping**: Downloading flyers from store websites or Publitas.
2.  **Preprocessing**: Splitting PDFs and downsampling images for OCR/LLM analysis.
3.  **Extraction**: Using Gemini (and previously Tesseract-style logic) to identify deals and bounding boxes (`box_2d`).
4.  **Database**: Storing results in `flyers.db` via `db.py`.

## The "Paper Trail"
Based on the code structure:
*   **`main.py`** (originally in the root) orchestrated the workflow.
*   **`PublitasScraper`** (`scrapers/publitas.py`) was a core dependency used to fetch flyers for **Albert Heijn**, **Jumbo**, and **Hoogvliet**.
*   **`AldiScraper`** (`scrapers/aldi.py`) handled Aldi-specific PDF downloads.
*   **`DirkScraper`** (`scrapers/dirk.py`) handled Dirk-specific flyer downloads.
*   **`extract_gemini.py`** performed the heavy lifting of structured data extraction from the processed pages.

> [!IMPORTANT]
> **Lost History**: Some of the very first scripts from this iteration were lost during reorganization, but the core logic remains in the `scrapers/` and `preprocess.py` files.
>
> **Missing Components** (from this folder snapshot):
> *   **`main.py`**: The orchestrator originally in the root.
> *   **`requirements.txt`**: The legacy dependency list (needed Gemini/Playwright).
> *   **`scripts/`**: Utility scripts like `export_for_ai.py` and `list_categories.py`.
> *   **`flyers.db`**: The SQLite database mentioned in the logic.

## Data
Flyer data and page snapshots were stored in the `Folders/` directory. This directory is ignored by git to keep the repository lightweight.
