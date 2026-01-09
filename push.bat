@echo off
title JuanBabes Push to Vercel
cd /d C:\Users\us\Desktop\juanbabes_project\frontend

echo ============================================================
echo PUSH TO VERCEL (JuanBabes)
echo ============================================================
echo.

echo Deploying to Vercel...
vercel --prod --yes

echo.
echo ============================================================
echo PUSH COMPLETE
echo Live: https://juanbabes-analytics.vercel.app
echo ============================================================
pause
