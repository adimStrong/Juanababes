# JuanBabes Analytics - Project Guide

## Quick Reference
- **Live**: https://juanbabes-analytics.vercel.app
- **Repo**: https://github.com/adimStrong/Juanababes.git
- **DB**: `data/juanbabes_analytics.db` (SQLite)
- **5 pages**: Jam, Ashley, Abi, Sena, Zell (Zell has NO API token - CSV only)

## Architecture (DO NOT CHANGE)
```
Facebook API  ──→  fetch_missing_posts.py  ──→  SQLite (post identity + engagement)
                                                       ↓
Meta CSV Export ──→ import_manual_exports.py ──→  SQLite (UPDATE views/reach + creates posts API can't reach)
                                                       ↓
                                            export_static_data.py → analytics-v2.json
                                                       ↓
                                            git push → vercel --prod → Live
```

### CRITICAL RULES
1. **API is source of truth for posts.** Posts are CREATED by `fetch_missing_posts.py` (API). CSV also creates posts the API can't reach (synthetic `csv_<md5>` IDs).
2. **CSV Post IDs are ALL broken.** Meta exports in E+ notation. NEVER use CSV Post IDs.
3. **CSV Page IDs also broken.** "Juanababe Sena" vs "Juana Babe Sena" — importer resolves by name with space-stripped fuzzy matching.
4. **CSV times are UTC.** DB times are PHT (UTC+8). CSV importer adds +8h before matching.
5. **Zell has no API token.** All Zell data comes from CSV only.
6. **API limit=25** with auto-retry (halves on error). Viral pages crash at higher limits.

## Daily Morning Workflow

### RECOMMENDED: Use `daily.bat` (one click does everything)
```
1. (Optional) Drop fresh CSV into: exports\from content manual Export\
2. Double-click daily.bat
```
`daily.bat` runs all 5 steps automatically with error checking:
1. Fetch new posts from API
2. Import CSV views/reach (if CSV files exist)
3. Clean up duplicates
4. Export static JSON data
5. Git push + Vercel deploy

### IMPORTANT:
- **Views/reach ONLY come from CSV**, NOT from the API. If views show 0, you need a fresh CSV.
- **Meta CSV has 2-3 day lag** on views/reach data. Recent posts will show 0 until next CSV.
- **API gives**: new posts + reactions/comments/shares (updates last 7 days of existing posts)
- **CSV gives**: views, reach (updates existing posts with higher values only, never creates posts)
- **Zell has no API token.** All Zell data comes from CSV only.

### Weekly: Full engagement refresh
```
python refresh_engagement.py          # Refresh ALL posts
python refresh_engagement.py --month  # Refresh current month only
```

### Bat files:
- `daily.bat` — **USE THIS** — full pipeline (API + CSV + cleanup + export + deploy)
- `update_csv.bat` — imports CSV views/reach + exports JSON (standalone)
- `update_api.bat` — fetches API posts + updates engagement + exports JSON (standalone)
- `push.bat` — cleanup + export + git push + vercel deploy (standalone)
- `refresh_engagement.py` — parallel API refresh of ALL posts (run weekly)

## File Locations
- **CSV exports**: `exports/from content manual Export/*.csv`
- **Page tokens**: `page_tokens.json` (60-day expiry, 4 pages - NO Zell)
- **Frontend data**: `frontend/public/data/analytics-v2.json`
- **DB**: `data/juanbabes_analytics.db`

## Common Issues & Fixes

### "Views/reach showing 0 or dropping"
- CSV hasn't been imported, or CSV doesn't cover those dates
- Export fresh CSV from Meta, drop in exports folder, run `update_csv.bat`

### "Page name mismatch (Juanababe vs Juana Babe)"
- Importer uses space-stripped fuzzy matching — should auto-resolve
- If not, check `page_lookup` in import_manual_exports.py

### "API error: reduce data"
- Viral pages (like Sena) cause this at high limits
- Already fixed: limit=25 with auto-retry (halves to 12→5 on error)

### "Token expired"
- Page tokens expire every 60 days
- Update `page_tokens.json` with fresh tokens

## Key Metrics
- **PES** = Reactions×1 + Comments×2 + Shares×3
- **Engagement** = Reactions + Comments + Shares
