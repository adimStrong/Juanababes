@echo off
title JuanBabes Daemon
cd /d C:\Users\us\Desktop\juanbabes_project

echo ============================================================
echo JUANBABES DAEMON
echo ============================================================
echo.
echo Schedule:
echo   - Every hour: Fetch API + notify new posts
echo   - At 6:00 AM: Export + push to Vercel
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

python juanbabes_daemon.py

pause
