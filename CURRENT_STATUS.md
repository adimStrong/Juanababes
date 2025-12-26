# JuanBabes Analytics Dashboard - Current Status

## Project Location
`C:\Users\us\Desktop\juanbabes_project`

## GitHub Repo
https://github.com/adimStrong/Juanababes

---

## What's Done

### Data Collection
- 5 Facebook Pages imported from CSV exports (Meta Business Suite)
- 594 posts total with engagement metrics
- Data range: October 2025 - December 2025

### The 5 JuanBabes Pages
| Page | Posts | Engagement | Avg/Post |
|------|-------|------------|----------|
| Ashley | 115 | 68,309 | 594 |
| Sena | 240 | 40,780 | 170 |
| Abi | 105 | 11,242 | 107 |
| Zell | 71 | 9,075 | 128 |
| Jam | 63 | 7,138 | 113 |

### Backend (Django)
- Django REST Framework API at `backend/`
- SQLite database at `data/juanbabes_analytics.db`
- Endpoints: `/api/stats/`, `/api/stats/pages/`, `/api/stats/post-types/`, etc.

### Frontend (React)
- React + Vite + Tailwind CSS at `frontend/`
- Dashboard with charts (Recharts)
- Page comparison, post type distribution, daily engagement
- Static data export for Vercel deployment

### CSV Reports
- `reports/page_comparison.csv`
- `reports/all_posts.csv`
- `reports/daily_engagement.csv`
- `reports/top_50_posts.csv`

---

## What's Pending

### Vercel Deployment
1. Go to: https://vercel.com/new
2. Import from GitHub: `adimStrong/Juanababes`
3. Set **Root Directory**: `frontend`
4. Set **Project Name**: `juanbabes-dashboard`
5. Framework: Vite (auto-detect)
6. Click Deploy

---

## How to Run Locally

### Backend
```bash
cd backend
python manage.py runserver 8001
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Export CSV Reports
```bash
python export_report.py
```

---

## Key Files
- `frontend/public/data/analytics.json` - Static data for Vercel
- `data/juanbabes_analytics.db` - SQLite database
- `page_tokens.json` - Facebook page tokens (60-day validity)
- `export_report.py` - CSV export script

---

## Resume Prompt
"Continue working on JuanBabes Analytics Dashboard. Deploy frontend to Vercel using the GitHub repo https://github.com/adimStrong/Juanababes. Set root directory to 'frontend' and project name to 'juanbabes-dashboard'."
