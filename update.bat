@echo off
title JuanBabes Update
cd /d C:\Users\us\Desktop\juanbabes_project

echo ============================================================
echo JUANBABES UPDATE
echo ============================================================
echo.
echo [1/2] Importing CSV files...
python csv_importer.py import-all "exports/from content manual Export"

echo.
echo [2/2] Exporting analytics...
python export_static_data.py

echo.
echo ============================================================
echo UPDATE COMPLETE
echo.
echo Data updated locally. To push to Vercel, run: push.bat
echo ============================================================
pause
