@echo off
echo ========================================================
echo BOODSCHAPPEN PIPELINE (HIGH-FIDELITY ARCHIVE)
echo ========================================================
echo.

echo [1/3] Step 1: Running Scraper Engine (Parallel Modes)...
echo Gathering deals with 5s hydration wait across all stores.
C:\Users\Deuts\tudelft-conda\python.exe scripts\run_pipeline.py
if %errorlevel% neq 0 (
    echo [ERROR] Scraper failed! Please check logs.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/3] Step 2: Running AI Enrichment (Mistral)...
echo Categorizing items and calculating Unit Prices.
C:\Users\Deuts\tudelft-conda\python.exe scripts\enrich_deals.py
if %errorlevel% neq 0 (
    echo [ERROR] AI Enrichment failed! 
    pause
    exit /b %errorlevel%
)

echo.
echo [3/3] Step 3: Launching Historical Grid Dashboard
echo Head over to your browser (http://127.0.0.1:5000) to view deals.
C:\Users\Deuts\tudelft-conda\python.exe web_app\app.py

pause
