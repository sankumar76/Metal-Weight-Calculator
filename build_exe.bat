@echo off
REM Builds dist\WeightCalculator.exe -- a single file you can share; users need nothing else installed.
cd /d "%~dp0"

python -m pip install --upgrade pyinstaller pillow || goto :error
python tools\make_icon.py || goto :error

python -m PyInstaller --noconfirm --clean --onefile --windowed ^
    --name WeightCalculator ^
    --icon assets\icon.ico ^
    --add-data "assets;assets" ^
    --version-file version_info.txt ^
    --exclude-module numpy ^
    main.py || goto :error

echo.
echo Done: dist\WeightCalculator.exe
pause
exit /b 0

:error
echo.
echo Build failed.
pause
exit /b 1
