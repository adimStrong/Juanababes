# JuanBabes Analytics Dashboard - Project Prompt

Use this prompt to continue working on the JuanBabes project with Claude or another AI assistant.

---

## Project Context Prompt

```
I have a JuanBabes Analytics Dashboard project at:
C:\Users\us\Desktop\juanbabes_project

## Project Overview
- Social media analytics dashboard for 5 Facebook pages (Juana Babe Ashley, Sena, Abi, Zell, Jam)
- Imports data from Meta Business Suite CSV exports
- Stores data in SQLite database
- React + Vite frontend deployed on Railway
- Static JSON data for production (no live backend needed)

## Tech Stack
- Backend: Python (csv_importer.py, database.py, export_static_data.py)
- Frontend: React + Vite + Tailwind CSS + Recharts
- Database: SQLite (data/juanbabes_analytics.db)
- Deployment: Railway (auto-deploy from GitHub main branch)

## Key Files
- csv_importer.py: Import Meta CSV exports (converts UTC to PHT timezone)
- database.py: SQLite operations, metrics sync
- export_static_data.py: Generate analytics.json for frontend
- frontend/src/pages/Dashboard.jsx: Main analytics dashboard
- frontend/src/services/api.js: Data loading (uses static JSON in production)
- update_report.bat: One-click import, export, and deploy

## Data Flow
1. Export CSV from Meta Business Suite
2. Place in exports/from content manual Export/
3. Run: python csv_importer.py import-all "exports/from content manual Export" --mode merge
4. Run: python export_static_data.py
5. Push to GitHub for Railway auto-deploy

## Important Notes
- Timestamps are converted from UTC to PHT (+8 hours) during import
- Dashboard shows data up to "today - 2 days" (incomplete data filtered)
- Metrics stored in post_metrics table, synced to posts table before export

## Current Stats
- 5 pages, 618 posts, 87 days of data
- Date range: Oct 1, 2025 - Dec 26, 2025
- Total engagement: 150,147

## Dashboard URL
https://juanababes-production.up.railway.app/
```

---

## Quick Reference Commands

### Import New Data
```bash
cd /c/Users/us/Desktop/juanbabes_project
python csv_importer.py import-all "exports/from content manual Export" --mode merge
```

### Export Analytics
```bash
python export_static_data.py
```

### View Database Stats
```bash
python csv_importer.py stats
```

### Full Update (Import + Export + Push)
```bash
update_report.bat
```

Or manually:
```bash
python csv_importer.py import-all "exports/from content manual Export" --mode merge && \
python export_static_data.py && \
git add -A && git commit -m "Update report" && git push origin main
```

---

## Common Tasks

### Add new CSV data
1. Place CSV in `exports/from content manual Export/`
2. Run `update_report.bat` or manual commands above

### Fix timezone issues
The csv_importer.py already converts UTC to PHT. If needed:
```python
# In csv_importer.py
PHT_OFFSET = timedelta(hours=8)  # UTC+8
```

### Modify date filtering
In `frontend/src/services/api.js`, change the cutoff:
```javascript
cutoffDate.setDate(cutoffDate.getDate() - 2);  // Change -2 to desired days
```

### Add new chart
1. Add data function in `frontend/src/services/api.js`
2. Add chart component in `frontend/src/pages/Dashboard.jsx`
3. Use Recharts library for visualization

---

## Database Schema

### posts table
```sql
post_id TEXT PRIMARY KEY
page_id TEXT
title TEXT
post_type TEXT
publish_time TEXT  -- Format: MM/DD/YYYY HH:MM (PHT)
permalink TEXT
reactions_total INTEGER
comments_count INTEGER
shares_count INTEGER
views_count INTEGER
reach_count INTEGER
total_engagement INTEGER
```

### post_metrics table
```sql
id INTEGER PRIMARY KEY
post_id TEXT
metric_date TEXT
reactions INTEGER
comments INTEGER
shares INTEGER
views INTEGER
reach INTEGER
source TEXT  -- csv, api, scraped
```

### pages table
```sql
page_id TEXT PRIMARY KEY
page_name TEXT
page_url TEXT
fan_count INTEGER
```

---

## GitHub Repository
https://github.com/adimStrong/Juanababes

## Deployment
- Railway auto-deploys from `main` branch
- No manual deployment needed - just push to GitHub

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Charts empty | Run `export_static_data.py` and push |
| Wrong dates | Re-import CSVs (they convert UTC to PHT) |
| Data not updating | Check CSV path, run full update |
| Git push failed | Check credentials, retry |
| Missing Dec 26 data | Timezone fix was applied Dec 27 |
