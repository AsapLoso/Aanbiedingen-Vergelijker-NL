@echo off
setlocal

REM 1. Try direct Anaconda Python (avoids activation prompt)
if exist "C:\Users\Deuts\anaconda3\python.exe" (
    echo Found Anaconda Python. Using directly...
    set PYTHON_CMD="C:\Users\Deuts\anaconda3\python.exe"
    goto :RUN_PY
)

REM 1b. Fallback to activation if needed (legacy)
if exist "C:\Users\Deuts\anaconda3\Scripts\activate.bat" (
    echo Found Anaconda activate script. Activating base environment...
    call "C:\Users\Deuts\anaconda3\Scripts\activate.bat"
    goto :RUN
)

REM 2. Try standard Python
python --version >nul 2>nul
if %errorlevel% equ 0 (
    echo Found standard Python.
    goto :RUN
)

REM 3. Try 'py' launcher
py --version >nul 2>nul
if %errorlevel% equ 0 (
    echo Found Python Launcher (py).
    set PYTHON_CMD=py
    goto :RUN_PY
)

echo.
echo CRITICAL ERROR: Python not found!
echo.
echo Please install Python from python.org or ensure Anaconda is installed correctly.
pause
exit /b

:RUN
set PYTHON_CMD=python

:RUN_PY
echo Using Python: %PYTHON_CMD%
%PYTHON_CMD% --version

echo.
echo Installing requirements...
%PYTHON_CMD% -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo Failed to install requirements.
    pause
    exit /b
)

echo.
echo Installing Playwright browsers...
%PYTHON_CMD% -m playwright install
if %errorlevel% neq 0 (
    echo.
    echo Failed to install Playwright.
    pause
    exit /b
)

echo.
echo ==========================================
echo       Grocery Flyer Scraper Selection
echo ==========================================
echo [0] All Stores
echo [1] Aldi
echo [2] Dirk
echo [3] Albert Heijn
echo [4] Jumbo
echo [4] Jumbo
echo.
echo Example: "124" for Aldi, Dirk, and Jumbo.
echo Example: "0" for All.
echo.
set /p selection="Select stores to scrape (default 0): "

if "%selection%"=="" set selection=0

set /p force="Force download new flyers? (y/N): "
set FORCE_FLAG=
if /i "%force%"=="y" set FORCE_FLAG=--force

set /p force_pp="Force re-process existing pages? (y/N): "
set FORCE_PP_FLAG=
if /i "%force_pp%"=="y" set FORCE_PP_FLAG=--force-preprocess

set /p run_extract="Extract data with Gemini? (y/N): "
set EXTRACT_FLAG=
if /i "%run_extract%"=="y" (
    set model_name=models/gemini-2.5-pro
    set EXTRACT_FLAG=--extract --model "models/gemini-2.5-pro"
)

set /p debug_mode="Enable visual debugging (draw bounding boxes)? (y/N): "
set DEBUG_FLAG=
if /i "%debug_mode%"=="y" set DEBUG_FLAG=--visualize

set /p run_export="Export for AI Categorization? (y/N): "

echo.
echo ==========================================
echo Starting Workflow...
echo ==========================================

echo.
echo [1/4] Running Scrapers...
%PYTHON_CMD% main.py --scrape --stores "%selection%" %FORCE_FLAG%

echo.
echo [2/4] Running Preprocessing...
%PYTHON_CMD% main.py --preprocess --stores "%selection%" %FORCE_PP_FLAG%

if defined EXTRACT_FLAG (
    echo.
    echo [3/4] Running Extraction...
    %PYTHON_CMD% main.py %EXTRACT_FLAG% --stores "%selection%"
) else (
    echo.
    echo [3/4] Skipping Extraction...
)

if defined DEBUG_FLAG (
    echo.
    echo [4/4] Running Visual Debugging...
    %PYTHON_CMD% main.py %DEBUG_FLAG% --stores "%selection%"
) else (
    echo.
    echo [4/4] Skipping Visual Debugging...
)

if /i "%run_export%"=="y" (
    echo.
    echo [5/5] Exporting for AI Categorization...
    %PYTHON_CMD% scripts/export_for_ai.py
)

echo.
echo Done.
pause
