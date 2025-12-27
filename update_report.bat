@echo off
cd /d C:\Users\us\Desktop\juanbabes_project

echo ============================================
echo JuanBabes Report Update - %date% %time%
echo ============================================

REM Step 1: Import all CSVs from manual export folder
echo [1/4] Importing CSV data...
python csv_importer.py import-all "exports\from content manual Export" --mode merge

REM Step 2: Export static data for frontend
echo [2/4] Exporting analytics data...
python export_static_data.py

REM Step 3: Git commit and push
echo [3/4] Pushing to GitHub...
git add -A
git commit -m "Report update: %date% - CSV import and analytics refresh"
git push origin main

REM Step 4: Notify user
echo [4/4] Sending notification...
powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Report has been updated and pushed to GitHub!', 'JuanBabes Update Complete', 'OK', 'Information')"

echo ============================================
echo DONE! Report updated and deployed.
echo ============================================
pause
