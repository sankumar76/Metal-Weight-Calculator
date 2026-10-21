@echo off
cd /d "%~dp0"
python -c "import PIL" 2>nul || python -m pip install -r requirements.txt
python main.py
if errorlevel 1 (
    echo.
    echo Something went wrong. Make sure Python 3.8+ is installed and on PATH.
    pause
)
