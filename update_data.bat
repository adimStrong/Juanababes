@echo off
echo ============================================================
echo JuanBabes Data Update Tool
echo ============================================================
echo.
echo Workflow: CSV data is PRIORITY (has views/reach)
echo           FB API fills gaps for missing dates
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/5] Importing posts from CSV (priority data)...
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

echo [2/5] Fetching missing posts from FB API (fills gaps)...
python fetch_missing_posts.py
if errorlevel 1 (
    echo WARNING: Missing posts fetch failed (tokens may be expired)
)
echo Done.
echo.

echo [3/5] Fetching comment analysis from FB API...
python fetch_comments.py
if errorlevel 1 (
    echo WARNING: Comment fetch failed (tokens may be expired)
)
echo Done.
echo.

echo [4/5] Exporting analytics to JSON...
python export_static_data.py
if errorlevel 1 (
    echo ERROR: Export failed
    pause
    exit /b 1
)
echo Done.
echo.

echo [5/5] Committing and pushing to GitHub...
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
