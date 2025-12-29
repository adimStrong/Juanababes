@echo off
echo ============================================================
echo JuanBabes Data Update Tool
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/4] Importing posts from CSV...
echo.
dir /b "exports\from content manual Export\*.csv" 2>nul
echo.
python import_manual_exports.py
if errorlevel 1 (
    echo ERROR: CSV import failed
    pause
    exit /b 1
)
echo Done.
echo.

echo [2/4] Fetching comment analysis from FB API...
python fetch_comments.py
if errorlevel 1 (
    echo WARNING: Comment fetch failed (tokens may be expired)
)
echo Done.
echo.

echo [3/4] Exporting analytics to JSON...
python export_static_data.py
if errorlevel 1 (
    echo ERROR: Export failed
    pause
    exit /b 1
)
echo Done.
echo.

echo [4/4] Committing and pushing to GitHub...
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
