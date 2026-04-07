---
description: Full Grocery Pipeline (Scrape -> Enrich -> Dashboard)
---
// turbo-all

1. **Scrape Fresh Data**: Pull new deals and capture raw HTML audit snippets.
```bash
C:\Users\Deuts\tudelft-conda\python.exe scripts/run_pipeline.py --no-future
```

2. **Debug: Verify Scrape**: Check how many raw deals were captured and if raw_html is present.
```bash
sqlite3 data/deals.db "SELECT store, COUNT(*), COUNT(raw_html) FROM deals GROUP BY store;"
```

3. **Enrich Deals**: Run the AI enrichment logic (Mistral-7B) to categorize and clean names.
```bash
C:\Users\Deuts\tudelft-conda\python.exe scripts/enrich_deals.py
```

4. **Debug: Verify Enrichment**: Check the counts of generic names and categories assigned.
```bash
sqlite3 data/deals.db "SELECT category, COUNT(*) FROM deals WHERE category IS NOT NULL GROUP BY category;"
```

5. **Launch Dashboard**: Start the proprietary grid interface.
```bash
C:\Users\Deuts\tudelft-conda\python.exe web_app/app.py
```
