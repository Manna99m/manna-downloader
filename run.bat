@echo off
title Manna Downloader
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo Python 3.10+ is required.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt

echo.
echo Manna Downloader is starting...
echo Open http://127.0.0.1:8000
echo.
".venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
