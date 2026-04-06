@echo off
setlocal

REM 1. Try to activate Anaconda environment
if exist "C:\Users\Deuts\anaconda3\Scripts\activate.bat" (
    echo Found Anaconda. Activating base environment...
    call "C:\Users\Deuts\anaconda3\Scripts\activate.bat"
    python scripts/list_categories.py
    goto :END
)

REM 2. Try standard Python
python scripts/list_categories.py
if %errorlevel% equ 0 goto :END

REM 3. Try 'py' launcher
py scripts/list_categories.py
if %errorlevel% equ 0 goto :END

REM 4. Try 'python3'
python3 scripts/list_categories.py

:END
pause
