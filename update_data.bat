@echo off
echo ============================================================
echo JuanBabes Data Update Tool
echo ============================================================
echo.

cd /d "%~dp0"

echo Choose update method:
echo [1] Fetch from Facebook API (uses page_tokens.json)
echo [2] Import from CSV (uses exports folder)
echo.
set /p choice="Enter 1 or 2: "

if "%choice%"=="1" goto :FETCH_API
if "%choice%"=="2" goto :IMPORT_CSV
echo Invalid choice
pause
exit /b 1

:FETCH_API
echo.
echo [1/3] Fetching data from Facebook API...
python fetch_all_pages.py
if errorlevel 1 (
    echo ERROR: API fetch failed. Tokens may be expired.
    echo To refresh tokens, visit: https://developers.facebook.com/tools/explorer/
    pause
    exit /b 1
)
echo Done.
echo.
goto :EXPORT

:IMPORT_CSV
echo.
echo Looking for CSV files in exports folder...
dir /b "exports\from content manual Export\*.csv" 2>nul
echo.
echo [1/3] Importing CSV to database...
python import_manual_exports.py
if errorlevel 1 (
    echo ERROR: Import failed
    pause
    exit /b 1
)
echo Done.
echo.
goto :EXPORT

:EXPORT
echo [2/3] Exporting analytics to JSON...
python export_static_data.py
if errorlevel 1 (
    echo ERROR: Export failed
    pause
    exit /b 1
)
echo Done.
echo.

echo [3/3] Committing and pushing to GitHub...
set GIT="C:\Users\us\AppData\Local\Programs\Git\bin\git.exe"
%GIT% add frontend/public/data/analytics.json
%GIT% commit -m "Update analytics data - %date%"
%GIT% push origin main
echo Done.
echo.

echo ============================================================
echo SUCCESS! Data has been updated and deployed.
echo ============================================================
echo.
pause
