@echo off
setlocal

cd /d "%~dp0"

echo =====================================
echo   Finance Transaction Dashboard Startup
echo =====================================

echo [1] Checking Python...
where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found.
    pause
    exit /b 1
)

echo [2] Creating venv if not exists...
if not exist ".venv\Scripts\activate.bat" (
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create venv.
        pause
        exit /b 1
    )
)

echo [3] Activating venv...
call .venv\Scripts\activate.bat

echo [4] Upgrading pip...
python -m pip install --upgrade pip

echo [5] Installing dependencies...
if exist requirements.txt (
    python -m pip install -r requirements.txt
) else (
    echo No requirements.txt found. Skipping dependency install.
)

echo [6] Starting product UI...
start "Finance Transaction Dashboard" cmd /k "cd /d "%~dp0" && call .venv\Scripts\activate.bat && python app.py --serve"

timeout /t 2 >nul
start http://127.0.0.1:8007/

echo.
echo Finance Transaction Dashboard is running at http://127.0.0.1:8007/
echo.

pause
endlocal