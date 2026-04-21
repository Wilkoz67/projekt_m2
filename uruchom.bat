@echo off
cd /d "%~dp0"

echo Sprawdzam wymagane biblioteki...
pip install -r requirements.txt --quiet

echo Uruchamianie projektu...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo BLAD: Cos poszlo nie tak!
    pause
)
