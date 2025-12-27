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

## Deployment Options

### Option 1: Vercel (Frontend Only - Static Data)
Uses pre-exported JSON data, no live API needed.

1. Go to: https://vercel.com/new
2. Import from GitHub: `adimStrong/Juanababes`
3. Set **Root Directory**: `frontend`
4. Set **Project Name**: `juanbabes-dashboard`
5. Framework: Vite (auto-detect)
6. Click Deploy

### Option 2: Railway (Full Stack - Live API)
Deploy both Django backend and React frontend with live database.

#### Backend Deployment:
1. Go to: https://railway.app/new
2. Deploy from GitHub: `adimStrong/Juanababes`
3. Set **Root Directory**: `backend`
4. Add environment variables:
   ```
   DJANGO_SECRET_KEY=your-secret-key
   DEBUG=False
   ALLOWED_HOSTS=*.railway.app
   ```
5. Set **Start Command**: `python manage.py migrate && gunicorn juanbabes.wsgi`

#### Frontend Deployment:
1. Add another service in Railway
2. Set **Root Directory**: `frontend`
3. Set **Build Command**: `npm install && npm run build`
4. Set **Start Command**: `npx serve dist -s`
5. Add environment variable:
   ```
   VITE_API_URL=https://your-backend.railway.app/api
   ```

#### Database:
- Add PostgreSQL plugin in Railway
- Update Django settings for PostgreSQL

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

## Resume Prompts

### For Vercel Deployment:
"Deploy JuanBabes frontend to Vercel. GitHub repo: https://github.com/adimStrong/Juanababes. Root directory: frontend. Project name: juanbabes-dashboard. Use MCP Playwright to automate the setup."

### For Railway Deployment:
"Deploy JuanBabes full stack to Railway. GitHub repo: https://github.com/adimStrong/Juanababes. Deploy backend (Django) and frontend (React) as separate services. Use MCP Playwright to automate the setup."

### For Local Development:
"Continue working on JuanBabes Analytics Dashboard at C:\Users\us\Desktop\juanbabes_project. Run backend on port 8001 and frontend on port 5173."
