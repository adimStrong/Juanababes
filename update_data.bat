@echo off
echo ============================================================
echo JuanBabes Data Update Tool
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if CSV file was provided as argument
if "%~1"=="" (
    echo Usage: Drag and drop a CSV file onto this batch file
    echo        OR run: update_data.bat "path\to\your\file.csv"
    echo.
    echo Looking for recent CSVs in Downloads folder...
    echo.
    for /f "tokens=*" %%i in ('dir /b /o-d "%USERPROFILE%\Downloads\*.csv" 2^>nul') do @echo %%i
    echo.
    pause
    exit /b 1
)

set CSV_FILE=%~1
echo CSV File: %CSV_FILE%
echo.

REM Step 1: Copy CSV to exports folder
echo [1/4] Copying CSV to exports folder...
if not exist "exports\from content manual Export" mkdir "exports\from content manual Export"
copy "%CSV_FILE%" "exports\from content manual Export\" /Y
if errorlevel 1 (
    echo ERROR: Failed to copy CSV file
    pause
    exit /b 1
)
echo Done.
echo.

REM Step 2: Import CSV to database
echo [2/4] Importing CSV to database...
python import_manual_exports.py
if errorlevel 1 (
    echo ERROR: Import failed
    pause
    exit /b 1
)
echo Done.
echo.

REM Step 3: Export static data to JSON
echo [3/4] Exporting analytics to JSON...
python export_static_data.py
if errorlevel 1 (
    echo ERROR: Export failed
    pause
    exit /b 1
)
echo Done.
echo.

REM Step 4: Git commit and push
echo [4/4] Committing and pushing to GitHub...
git add frontend/public/data/analytics.json
git commit -m "Update analytics data - %date%"
git push origin main
echo Done.
echo.

echo ============================================================
echo SUCCESS! Data has been updated and deployed.
echo ============================================================
echo.
pause
