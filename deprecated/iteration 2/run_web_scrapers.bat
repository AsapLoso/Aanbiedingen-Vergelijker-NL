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
echo       Running Web Scrapers
echo ==========================================
echo.
echo This will scrape deals directly from:
echo - Dirk
echo - Albert Heijn (Headful mode)
echo - Aldi
echo - Jumbo
echo - Hoogvliet
echo.
echo NOTE: A browser window will open for Albert Heijn. Do not close it manually.
echo.

%PYTHON_CMD% main.py --web

echo.
echo Done.
pause
