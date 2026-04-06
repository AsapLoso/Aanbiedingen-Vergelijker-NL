# Iteration 2: Web-based Approach (Legacy)

This directory contains the transition to direct web scraping, bypassing the need for PDF flyer parsing.

## Overview
The web-based iteration aimed for direct data extraction from the supermarkets' websites:
1.  **Direct Scraping**: Using Playwright or BeautifulSoup to fetch product and price info.
2.  **Web Database**: Using `web_db.py` and `web_deals.db` for storage.
3.  **Visualization**: Generating large HTML snapshots like `index.html` (72MB) for manual review.

## Key Files
*   **`scrapers/`**: Contains the `_web.py` versions of store scrapers.
*   **`main.py`**: The central entry point (moved here) activated via the `--web` flag.
*   **`generate_web.py`**: Exports the scraped web data into a consolidated HTML report.
*   **`run_web_scrapers.bat`**: Automates the multi-store web scrape.

> [!NOTE]
> **Data Management**: This iteration generated large HTML exports (notably `index.html`). These are ignored in version control via the `.gitignore`.
>
> **Consolidated Snapshot**: This folder has been updated with the core modules from **Iteration 1** (`preprocess.py`, `extract_gemini.py`, `visualize.py`). It is now a **fully functional and self-contained** record of the project's state during the transition from flyer-parsing to web-scraping.
> *   **`run.bat`**: Restored legacy entry point for PDF processing.
> *   **`run_web_scrapers.bat`**: Entry point for the (then-new) web scraping method.
> *   **`requirements.txt`**: Consolidated dependency list for both methods.

## Architecture
This approach was faster but more fragile, as it relied on CSS selectors that changed frequently. It eventually led to the current, more specialized `scraper/` and `LLM/` based pipeline.
