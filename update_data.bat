@echo off
echo ============================================================
echo JuanBabes Data Update Tool
echo ============================================================
echo.

cd /d "%~dp0"

echo Looking for CSV files in exports folder...
echo.
dir /b "exports\from content manual Export\*.csv" 2>nul
echo.

echo [1/2] Importing CSV to database...
python import_manual_exports.py
if errorlevel 1 (
    echo ERROR: Import failed
    pause
    exit /b 1
)
echo Done.
echo.

echo [2/2] Exporting analytics to JSON...
python export_static_data.py
if errorlevel 1 (
    echo ERROR: Export failed
    pause
    exit /b 1
)
echo Done.
echo.

echo [3/3] Committing and pushing to GitHub...
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
