@echo off
title JuanBabes Fetch API
cd /d C:\Users\us\Desktop\juanbabes_project

echo ============================================================
echo FETCH FROM FACEBOOK API
echo ============================================================
echo.

python fetch_missing_posts.py --no-notify

echo.
echo [2/2] Exporting data...
python export_static_data.py

echo.
echo ============================================================
echo FETCH COMPLETE
echo ============================================================
pause
