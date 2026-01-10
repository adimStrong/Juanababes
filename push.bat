@echo off
title JuanBabes Push to Vercel (via GitHub)
cd /d C:\Users\us\Desktop\juanbabes_project

set GIT="C:\Users\us\AppData\Local\Programs\Git\bin\git.exe"

echo ============================================================
echo PUSH TO VERCEL (JuanBabes) via GitHub
echo ============================================================
echo.

echo Adding changes...
%GIT% add -A

echo.
echo Committing changes...
%GIT% commit -m "Update data - %date% %time%"

echo.
echo Pushing to GitHub (auto-deploys to Vercel)...
%GIT% push origin main

echo.
echo ============================================================
echo PUSH COMPLETE
echo Vercel will auto-deploy from GitHub.
echo Live: https://juanbabes-analytics.vercel.app
echo ============================================================
pause
