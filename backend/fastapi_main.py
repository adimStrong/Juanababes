"""JuanBabes Analytics - FastAPI Application."""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

# Import database module
from database import db_connection, execute_query, USE_POSTGRES, ensure_initialized


# ============ Pydantic Models ============

class DashboardStats(BaseModel):
    total_posts: int = 0
    total_engagement: int = 0
    total_reactions: int = 0
    total_comments: int = 0
    total_shares: int = 0
    total_pages: int = 0
    avg_engagement_per_post: float = 0
    date_range: Dict[str, str] = {}


class DailyStats(BaseModel):
    date: str
    post_count: int = 0
    engagement: int = 0
    reactions: int = 0
    comments: int = 0
    shares: int = 0


class PostTypeStats(BaseModel):
    post_type: str
    count: int = 0
    total_engagement: int = 0
    avg_engagement: float = 0
    reactions: int = 0
    comments: int = 0
    shares: int = 0


class Page(BaseModel):
    page_id: str
    page_name: str
    fan_count: Optional[int] = 0
    followers_count: Optional[int] = 0
    post_count: Optional[int] = 0
    total_engagement: Optional[int] = 0
    total_views: Optional[int] = 0
    total_reach: Optional[int] = 0
    total_reactions: Optional[int] = 0
    total_comments: Optional[int] = 0
    total_shares: Optional[int] = 0
    avg_engagement: Optional[float] = 0
    avg_reach: Optional[int] = 0
    avg_views: Optional[int] = 0


class Post(BaseModel):
    post_id: str
    page_id: str
    page_name: Optional[str] = None
    title: Optional[str] = None
    post_type: Optional[str] = None
    publish_time: Optional[str] = None
    reactions_total: int = 0
    comments_count: int = 0
    shares_count: int = 0
    total_engagement: int = 0
    permalink: Optional[str] = None


class PostsResponse(BaseModel):
    posts: List[Post]
    total: int
    page: int
    per_page: int


# ============ App Setup ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting JuanBabes Analytics API...")
    print(f"Database: {'PostgreSQL' if USE_POSTGRES else 'SQLite'}")
    ensure_initialized()
    yield
    print("Shutting down...")


app = FastAPI(
    title="JuanBabes Analytics API",
    description="Facebook page analytics for JuanBabes pages",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ Health Check ============

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "juanbabes-analytics",
        "database": "postgresql" if USE_POSTGRES else "sqlite"
    }


# ============ Stats Routes ============

@app.get("/api/v1/stats/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get dashboard summary statistics."""
    with db_connection() as conn:
        where_clauses = []
        params = []

        if start_date:
            where_clauses.append("DATE(publish_time) >= ?")
            params.append(start_date)
        if end_date:
            where_clauses.append("DATE(publish_time) <= ?")
            params.append(end_date)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        cursor = execute_query(conn, f"""
            SELECT
                COUNT(*) as total_posts,
                COALESCE(SUM(total_engagement), 0) as total_engagement,
                COALESCE(SUM(reactions_total), 0) as total_reactions,
                COALESCE(SUM(comments_count), 0) as total_comments,
                COALESCE(SUM(shares_count), 0) as total_shares,
                MIN(DATE(publish_time)) as min_date,
                MAX(DATE(publish_time)) as max_date
            FROM posts
            WHERE {where_sql}
        """, tuple(params))

        row = cursor.fetchone()

        cursor2 = execute_query(conn, "SELECT COUNT(DISTINCT page_id) FROM pages")
        page_row = cursor2.fetchone()
        page_count = page_row[0] if page_row else 0

    total_posts = row[0] or 0 if row else 0
    total_engagement = row[1] or 0 if row else 0

    return DashboardStats(
        total_posts=total_posts,
        total_engagement=total_engagement,
        total_reactions=row[2] or 0 if row else 0,
        total_comments=row[3] or 0 if row else 0,
        total_shares=row[4] or 0 if row else 0,
        total_pages=page_count,
        avg_engagement_per_post=round(total_engagement / total_posts, 2) if total_posts > 0 else 0,
        date_range={"start": str(row[5] or "") if row else "", "end": str(row[6] or "") if row else ""},
    )


@app.get("/api/v1/stats/", response_model=DashboardStats)
async def get_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Alias for dashboard stats."""
    return await get_dashboard_stats(start_date, end_date)


@app.get("/api/v1/stats/daily", response_model=List[DailyStats])
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365),
    page_id: Optional[str] = None,
):
    """Get daily engagement statistics."""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    page_filter = ""
    params = [since_date]
    if page_id:
        page_filter = "AND page_id = ?"
        params.append(page_id)

    with db_connection() as conn:
        cursor = execute_query(conn, f"""
            SELECT
                DATE(publish_time) as date,
                COUNT(*) as post_count,
                COALESCE(SUM(total_engagement), 0) as engagement,
                COALESCE(SUM(reactions_total), 0) as reactions,
                COALESCE(SUM(comments_count), 0) as comments,
                COALESCE(SUM(shares_count), 0) as shares
            FROM posts
            WHERE DATE(publish_time) >= ? {page_filter}
            GROUP BY DATE(publish_time)
            ORDER BY date ASC
        """, tuple(params))

        rows = cursor.fetchall()

    return [
        DailyStats(
            date=str(row[0]),
            post_count=row[1],
            engagement=row[2],
            reactions=row[3],
            comments=row[4],
            shares=row[5],
        )
        for row in rows
    ]


@app.get("/api/v1/stats/post-types", response_model=List[PostTypeStats])
async def get_post_type_stats(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """Get statistics grouped by post type."""
    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("DATE(publish_time) >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("DATE(publish_time) <= ?")
        params.append(end_date)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with db_connection() as conn:
        cursor = execute_query(conn, f"""
            SELECT
                COALESCE(post_type, 'UNKNOWN') as post_type,
                COUNT(*) as count,
                COALESCE(SUM(total_engagement), 0) as total_engagement,
                COALESCE(SUM(reactions_total), 0) as reactions,
                COALESCE(SUM(comments_count), 0) as comments,
                COALESCE(SUM(shares_count), 0) as shares
            FROM posts
            WHERE {where_sql}
            GROUP BY post_type
            ORDER BY total_engagement DESC
        """, tuple(params))

        rows = cursor.fetchall()

    return [
        PostTypeStats(
            post_type=row[0],
            count=row[1],
            total_engagement=row[2],
            avg_engagement=round(row[2] / row[1], 2) if row[1] > 0 else 0,
            reactions=row[3] or 0,
            comments=row[4] or 0,
            shares=row[5] or 0,
        )
        for row in rows
    ]


@app.get("/api/v1/stats/top-posts", response_model=List[Post])
async def get_top_posts(
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(365, ge=1, le=730),
):
    """Get top performing posts."""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    with db_connection() as conn:
        cursor = execute_query(conn, """
            SELECT
                p.post_id,
                p.page_id,
                pg.page_name,
                p.title,
                p.post_type,
                p.publish_time,
                p.reactions_total,
                p.comments_count,
                p.shares_count,
                p.total_engagement,
                p.permalink
            FROM posts p
            LEFT JOIN pages pg ON p.page_id = pg.page_id
            WHERE DATE(p.publish_time) >= ?
            ORDER BY p.total_engagement DESC
            LIMIT ?
        """, (since_date, limit))

        rows = cursor.fetchall()

    return [
        Post(
            post_id=row[0],
            page_id=row[1],
            page_name=row[2],
            title=row[3],
            post_type=row[4],
            publish_time=str(row[5]) if row[5] else None,
            reactions_total=row[6] or 0,
            comments_count=row[7] or 0,
            shares_count=row[8] or 0,
            total_engagement=row[9] or 0,
            permalink=row[10],
        )
        for row in rows
    ]


@app.get("/api/v1/stats/time-series", response_model=List[DailyStats])
async def get_time_series(
    days: int = Query(30, ge=1, le=365),
    page_id: Optional[str] = None,
):
    """Get time series data for charts (alias for daily stats)."""
    return await get_daily_stats(days, page_id)


@app.get("/api/v1/stats/daily-by-page")
async def get_daily_by_page(days: int = Query(60, ge=1, le=365)):
    """Get daily post counts grouped by page (for stacked bar chart)."""
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    with db_connection() as conn:
        # Get all pages first
        cursor = execute_query(conn, "SELECT page_id, page_name FROM pages ORDER BY page_name")
        pages = {row[0]: row[1].replace('Juana Babe ', '') if row[1] else row[0] for row in cursor.fetchall()}

        # Get daily counts per page
        cursor = execute_query(conn, """
            SELECT
                DATE(publish_time) as date,
                page_id,
                COUNT(*) as count
            FROM posts
            WHERE DATE(publish_time) >= ?
            GROUP BY DATE(publish_time), page_id
            ORDER BY date ASC
        """, (since_date,))

        rows = cursor.fetchall()

    # Build date -> page -> count mapping
    date_data = {}
    for row in rows:
        date_str = str(row[0])
        page_id = row[1]
        count = row[2]
        page_name = pages.get(page_id, page_id)

        if date_str not in date_data:
            date_data[date_str] = {"date": date_str}
        date_data[date_str][page_name] = count

    # Convert to list and ensure all pages have values
    page_names = list(set(pages.values()))
    data = []
    for date_str in sorted(date_data.keys()):
        item = date_data[date_str]
        for page_name in page_names:
            if page_name not in item:
                item[page_name] = 0
        data.append(item)

    return {"data": data, "pageNames": page_names}


@app.get("/api/v1/stats/page-comparison")
async def get_page_comparison(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get page comparison statistics."""
    where_clauses = []
    params = []

    if start_date:
        where_clauses.append("DATE(p.publish_time) >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("DATE(p.publish_time) <= ?")
        params.append(end_date)

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with db_connection() as conn:
        cursor = execute_query(conn, f"""
            SELECT
                pg.page_id,
                pg.page_name,
                pg.fan_count,
                COUNT(p.post_id) as post_count,
                COALESCE(SUM(p.total_engagement), 0) as total_engagement,
                COALESCE(SUM(p.reactions_total), 0) as reactions,
                COALESCE(SUM(p.comments_count), 0) as comments,
                COALESCE(SUM(p.shares_count), 0) as shares
            FROM pages pg
            LEFT JOIN posts p ON pg.page_id = p.page_id AND {where_sql}
            GROUP BY pg.page_id, pg.page_name, pg.fan_count
            ORDER BY total_engagement DESC
        """, tuple(params))

        rows = cursor.fetchall()

    return [
        {
            "page_id": row[0],
            "page_name": row[1],
            "fan_count": row[2] or 0,
            "post_count": row[3] or 0,
            "total_engagement": row[4] or 0,
            "reactions": row[5] or 0,
            "comments": row[6] or 0,
            "shares": row[7] or 0,
            "avg_engagement": round(row[4] / row[3], 2) if row[3] > 0 else 0,
        }
        for row in rows
    ]


# ============ Pages Routes ============

@app.get("/api/v1/pages/", response_model=List[Page])
async def get_pages():
    """Get all pages with stats."""
    with db_connection() as conn:
        cursor = execute_query(conn, """
            SELECT
                p.page_id,
                p.page_name,
                p.fan_count,
                p.followers_count,
                COUNT(DISTINCT po.post_id) as post_count,
                COALESCE(SUM(po.total_engagement), 0) as total_engagement,
                COALESCE(SUM(po.views), 0) as total_views,
                COALESCE(SUM(po.reach), 0) as total_reach,
                COALESCE(SUM(po.reactions_total), 0) as total_reactions,
                COALESCE(SUM(po.comments_count), 0) as total_comments,
                COALESCE(SUM(po.shares_count), 0) as total_shares
            FROM pages p
            LEFT JOIN posts po ON p.page_id = po.page_id
            GROUP BY p.page_id, p.page_name, p.fan_count, p.followers_count
            ORDER BY total_engagement DESC
        """)

        rows = cursor.fetchall()

    return [
        Page(
            page_id=row[0],
            page_name=row[1],
            fan_count=row[2] or 0,
            followers_count=row[3] or 0,
            post_count=row[4] or 0,
            total_engagement=row[5] or 0,
            total_views=row[6] or 0,
            total_reach=row[7] or 0,
            total_reactions=row[8] or 0,
            total_comments=row[9] or 0,
            total_shares=row[10] or 0,
            avg_engagement=round((row[5] or 0) / row[4], 2) if row[4] and row[4] > 0 else 0,
            avg_reach=round((row[7] or 0) / row[4]) if row[4] and row[4] > 0 else 0,
            avg_views=round((row[6] or 0) / row[4]) if row[4] and row[4] > 0 else 0,
        )
        for row in rows
    ]


@app.get("/api/v1/pages/{page_id}", response_model=Page)
async def get_page(page_id: str):
    """Get a single page by ID."""
    with db_connection() as conn:
        cursor = execute_query(conn, """
            SELECT
                p.page_id,
                p.page_name,
                p.fan_count,
                p.followers_count,
                COUNT(DISTINCT po.post_id) as post_count,
                COALESCE(SUM(po.total_engagement), 0) as total_engagement,
                COALESCE(SUM(po.views), 0) as total_views,
                COALESCE(SUM(po.reach), 0) as total_reach,
                COALESCE(SUM(po.reactions_total), 0) as total_reactions,
                COALESCE(SUM(po.comments_count), 0) as total_comments,
                COALESCE(SUM(po.shares_count), 0) as total_shares
            FROM pages p
            LEFT JOIN posts po ON p.page_id = po.page_id
            WHERE p.page_id = ?
            GROUP BY p.page_id, p.page_name, p.fan_count, p.followers_count
        """, (page_id,))

        row = cursor.fetchone()

    if not row:
        return Page(page_id=page_id, page_name="Not Found")

    return Page(
        page_id=row[0],
        page_name=row[1],
        fan_count=row[2] or 0,
        followers_count=row[3] or 0,
        post_count=row[4] or 0,
        total_engagement=row[5] or 0,
        total_views=row[6] or 0,
        total_reach=row[7] or 0,
        total_reactions=row[8] or 0,
        total_comments=row[9] or 0,
        total_shares=row[10] or 0,
        avg_engagement=round((row[5] or 0) / row[4], 2) if row[4] and row[4] > 0 else 0,
        avg_reach=round((row[7] or 0) / row[4]) if row[4] and row[4] > 0 else 0,
        avg_views=round((row[6] or 0) / row[4]) if row[4] and row[4] > 0 else 0,
    )


# ============ Posts Routes ============

@app.get("/api/v1/posts/", response_model=PostsResponse)
async def get_posts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    page_id: Optional[str] = None,
    post_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
):
    """Get posts with filtering and pagination."""
    where_clauses = []
    params = []

    if page_id:
        where_clauses.append("p.page_id = ?")
        params.append(page_id)

    if post_type:
        where_clauses.append("p.post_type = ?")
        params.append(post_type)

    if start_date:
        where_clauses.append("DATE(p.publish_time) >= ?")
        params.append(start_date)

    if end_date:
        where_clauses.append("DATE(p.publish_time) <= ?")
        params.append(end_date)

    if search:
        where_clauses.append("p.title LIKE ?")
        params.append(f"%{search}%")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with db_connection() as conn:
        # Count total
        cursor = execute_query(conn, f"""
            SELECT COUNT(*)
            FROM posts p
            WHERE {where_sql}
        """, tuple(params))
        total = cursor.fetchone()[0]

        # Get posts
        offset = (page - 1) * per_page
        cursor = execute_query(conn, f"""
            SELECT
                p.post_id,
                p.page_id,
                pg.page_name,
                p.title,
                p.post_type,
                p.publish_time,
                p.reactions_total,
                p.comments_count,
                p.shares_count,
                p.total_engagement,
                p.permalink
            FROM posts p
            LEFT JOIN pages pg ON p.page_id = pg.page_id
            WHERE {where_sql}
            ORDER BY p.publish_time DESC
            LIMIT ? OFFSET ?
        """, tuple(params + [per_page, offset]))

        rows = cursor.fetchall()

    posts = [
        Post(
            post_id=row[0],
            page_id=row[1],
            page_name=row[2],
            title=row[3],
            post_type=row[4],
            publish_time=str(row[5]) if row[5] else None,
            reactions_total=row[6] or 0,
            comments_count=row[7] or 0,
            shares_count=row[8] or 0,
            total_engagement=row[9] or 0,
            permalink=row[10],
        )
        for row in rows
    ]

    return PostsResponse(
        posts=posts,
        total=total,
        page=page,
        per_page=per_page,
    )


@app.get("/api/v1/posts/latest", response_model=Post)
async def get_latest_post():
    """Get the most recent post."""
    with db_connection() as conn:
        cursor = execute_query(conn, """
            SELECT
                p.post_id,
                p.page_id,
                pg.page_name,
                p.title,
                p.post_type,
                p.publish_time,
                p.reactions_total,
                p.comments_count,
                p.shares_count,
                p.total_engagement,
                p.permalink
            FROM posts p
            LEFT JOIN pages pg ON p.page_id = pg.page_id
            ORDER BY p.publish_time DESC
            LIMIT 1
        """)

        row = cursor.fetchone()

    if not row:
        return Post(post_id="", page_id="")

    return Post(
        post_id=row[0],
        page_id=row[1],
        page_name=row[2],
        title=row[3],
        post_type=row[4],
        publish_time=str(row[5]) if row[5] else None,
        reactions_total=row[6] or 0,
        comments_count=row[7] or 0,
        shares_count=row[8] or 0,
        total_engagement=row[9] or 0,
        permalink=row[10],
    )


@app.get("/api/v1/posts/top", response_model=List[Post])
async def get_posts_top(
    limit: int = Query(10, ge=1, le=100),
    days: int = Query(365, ge=1, le=730),
):
    """Alias for top posts."""
    return await get_top_posts(limit, days)


# ============ Imports Route ============

@app.get("/api/v1/imports/")
async def get_imports():
    """Get import history (stub)."""
    return []


# ============ Overlaps Route ============

@app.get("/api/v1/overlaps/")
async def get_overlaps():
    """Get page overlaps (stub)."""
    return []


# ============ Frontend Serving ============

frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    # Serve static data files
    data_dir = frontend_dist / "data"
    if data_dir.exists():
        app.mount("/data", StaticFiles(directory=data_dir), name="data")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Don't intercept API routes
        if full_path.startswith("api/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not found")
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("fastapi_main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8001)), reload=True)
