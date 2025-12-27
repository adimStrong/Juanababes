# JuanBabes Analytics Dashboard

## Project Summary

**JuanBabes Analytics Dashboard** is a comprehensive social media analytics platform for tracking and analyzing Facebook page performance across 5 "Juana Babe" pages. The system imports data from Meta Business Suite CSV exports, processes engagement metrics, and displays insights through an interactive React dashboard.

### Key Features
- **CSV Import System**: Automated import of Meta Business Suite exports with timezone conversion (UTC to PHT)
- **Multi-Page Analytics**: Track 5 Facebook pages (Ashley, Sena, Abi, Zell, Jam) simultaneously
- **Real-time Dashboard**: Interactive charts showing engagement, views, reach, and content metrics
- **Time Series Analysis**: Daily, weekly, and monthly performance trends
- **Comment Analysis**: Self-comment detection and engagement effectiveness metrics
- **Audience Overlap Detection**: Analyze content similarity between pages

---

## Architecture Overview

```
juanbabes_project/
├── Backend (Python)
│   ├── csv_importer.py      # Import Meta CSV exports
│   ├── database.py          # SQLite database operations
│   ├── export_static_data.py # Generate analytics.json for frontend
│   ├── models.py            # Data models (Page, Post, Metrics)
│   ├── config.py            # Project configuration
│   └── update_report.bat    # One-click update script
│
├── Frontend (React + Vite)
│   ├── src/pages/
│   │   ├── Dashboard.jsx    # Main analytics dashboard
│   │   ├── Posts.jsx        # All posts listing
│   │   ├── Pages.jsx        # Page comparison
│   │   ├── Comments.jsx     # Comment analysis
│   │   └── Overlap.jsx      # Audience overlap
│   ├── src/services/api.js  # API/static data service
│   └── public/data/analytics.json # Static data for production
│
└── Database
    └── data/juanbabes_analytics.db # SQLite database
```

---

## Database Schema

### Tables

#### `pages`
| Column | Type | Description |
|--------|------|-------------|
| page_id | TEXT | Primary key |
| page_name | TEXT | Page display name |
| page_url | TEXT | Facebook page URL |
| fan_count | INTEGER | Total fans/likes |
| created_at | TEXT | Record creation date |

#### `posts`
| Column | Type | Description |
|--------|------|-------------|
| post_id | TEXT | Primary key |
| page_id | TEXT | Foreign key to pages |
| title | TEXT | Post title/message |
| post_type | TEXT | Photo, Video, Reel, Live, Link |
| publish_time | TEXT | Publish date (PHT) |
| permalink | TEXT | Facebook post URL |
| reactions_total | INTEGER | Total reactions |
| comments_count | INTEGER | Total comments |
| shares_count | INTEGER | Total shares |
| views_count | INTEGER | Total views |
| reach_count | INTEGER | Total reach |
| total_engagement | INTEGER | reactions + comments + shares |

#### `post_metrics`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| post_id | TEXT | Foreign key to posts |
| metric_date | TEXT | Date metrics were recorded |
| reactions | INTEGER | Reactions count |
| comments | INTEGER | Comments count |
| shares | INTEGER | Shares count |
| views | INTEGER | Views count |
| reach | INTEGER | Reach count |
| source | TEXT | csv, api, or scraped |

#### `import_history`
| Column | Type | Description |
|--------|------|-------------|
| import_id | INTEGER | Primary key |
| filename | TEXT | Imported CSV filename |
| import_date | TEXT | When import occurred |
| rows_imported | INTEGER | New rows added |
| rows_updated | INTEGER | Existing rows updated |

---

## Key Metrics

### Engagement
- **Total Engagement** = Reactions + Comments + Shares
- **PES (Post Engagement Score)** = Total Engagement (alternative naming)

### Performance Indicators
- **Views**: Total video/post views
- **Reach**: Unique users who saw the content
- **Avg Engagement**: Total engagement / Total posts

---

## Data Flow

```
Meta Business Suite
        ↓
    CSV Export
        ↓
csv_importer.py (UTC → PHT conversion)
        ↓
SQLite Database (juanbabes_analytics.db)
        ↓
export_static_data.py
        ↓
analytics.json (static data)
        ↓
React Dashboard (Vercel/Railway)
```

---

## Timezone Handling

Meta Business Suite exports timestamps in **UTC**. The system converts all timestamps to **Philippine Time (PHT = UTC+8)** during import:

```python
PHT_OFFSET = timedelta(hours=8)
dt_pht = dt + PHT_OFFSET
```

This ensures dates displayed in the dashboard match local Philippine time.

---

## Date Filtering

The dashboard shows data up to **today - 2 days** to exclude incomplete data:
- Today: Still accumulating metrics
- Yesterday: May have delayed updates
- Day before yesterday and earlier: Complete data

---

## API Endpoints (Static Mode)

In production, the frontend uses static JSON data. Key data functions:

| Function | Description |
|----------|-------------|
| `getStats(pageId)` | Overall statistics |
| `getDailyEngagement(days, pageId)` | Daily engagement data |
| `getPostTypeStats(pageId)` | Post type breakdown |
| `getTopPosts(limit, metric, pageId)` | Top performing posts |
| `getPages()` | All pages with stats |
| `getDailyByPage(days)` | Daily posts per page |
| `getTimeSeries()` | Monthly/weekly trends |
| `getCommentAnalysis()` | Comment effectiveness |

---

## File Descriptions

### Python Scripts

| File | Purpose |
|------|---------|
| `csv_importer.py` | Import Meta CSV exports, convert UTC to PHT |
| `database.py` | SQLite operations, metrics sync |
| `export_static_data.py` | Generate analytics.json for frontend |
| `models.py` | Python dataclasses for data models |
| `config.py` | Project paths and settings |
| `update_report.bat` | One-click import, export, and deploy |

### React Components

| File | Purpose |
|------|---------|
| `Dashboard.jsx` | Main analytics view with charts |
| `Posts.jsx` | Paginated post listing |
| `Pages.jsx` | Page comparison table |
| `Comments.jsx` | Comment analysis dashboard |
| `Overlap.jsx` | Audience overlap analysis |
| `StatCard.jsx` | Reusable stat card component |
| `Layout.jsx` | Navigation and layout wrapper |

---

## Deployment

### Railway (Backend/Full Stack)
- Auto-deploys from GitHub main branch
- URL: https://juanababes-production.up.railway.app/

### Vercel (Frontend Only)
- Static hosting with analytics.json
- Zero backend required in production

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLite path (default: data/juanbabes_analytics.db) |
| `VITE_API_URL` | API endpoint (dev only) |

---

## Commands Reference

### Import CSV
```bash
python csv_importer.py import-all "exports/from content manual Export" --mode merge
```

### Export Static Data
```bash
python export_static_data.py
```

### View Database Stats
```bash
python csv_importer.py stats
```

### One-Click Update
```bash
update_report.bat
```

---

## Current Data Summary

| Metric | Value |
|--------|-------|
| Total Pages | 5 |
| Total Posts | 618 |
| Date Range | Oct 1, 2025 - Dec 26, 2025 |
| Total Engagement | 150,147 |

### Pages
1. **Juana Babe Ashley** - 116 posts, 81,191 engagement (TOP)
2. **Juana Babe Sena** - 244 posts, 41,161 engagement
3. **Juana Babe Abi** - 108 posts, 11,402 engagement
4. **Juana Babe Zell** - 72 posts, 9,162 engagement
5. **Juana Babe Jam** - 64 posts, 7,231 engagement

---

## Troubleshooting

### Data not updating?
1. Check CSV files are in `exports/from content manual Export/`
2. Run `python csv_importer.py stats` to verify database
3. Run `python export_static_data.py` to regenerate analytics.json
4. Push to GitHub for Railway auto-deploy

### Dates look wrong?
- Ensure csv_importer.py has PHT_OFFSET = timedelta(hours=8)
- Re-import CSVs after timezone fix

### Charts empty?
- Check analytics.json has data in `daily.all` array
- Verify dates are in YYYY-MM-DD format

---

## Version History

| Date | Changes |
|------|---------|
| Dec 27, 2025 | Added PHT timezone conversion |
| Dec 27, 2025 | Added today-2 date filtering |
| Dec 27, 2025 | Added stacked bar chart for daily posts by page |
| Dec 26, 2025 | Fixed metrics sync from post_metrics to posts |
| Dec 25, 2025 | Fixed daily chart date format (MM/DD to YYYY-MM-DD) |
