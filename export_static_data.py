#!/usr/bin/env python3
"""
Export static JSON data for Vercel deployment.

Run this after importing new CSV data to update the Vercel deployment.
The output goes to frontend/public/data/analytics.json

Usage:
    python export_static_data.py
"""

import json
import sqlite3
from datetime import datetime

DATABASE_PATH = "data/juanbabes_analytics.db"
OUTPUT_PATH = "frontend/public/data/analytics.json"


def get_conn():
    return sqlite3.connect(DATABASE_PATH)


def export_stats():
    """Export dashboard stats (all pages + per-page)."""
    conn = get_conn()
    cursor = conn.cursor()

    # Get all pages first
    cursor.execute("SELECT DISTINCT page_id FROM posts WHERE reactions_total > 0")
    page_ids = [row[0] for row in cursor.fetchall()]

    # Aggregate stats
    cursor.execute("""
        SELECT
            COALESCE(SUM(reactions_total), 0) as total_reactions,
            COALESCE(SUM(comments_count), 0) as total_comments,
            COALESCE(SUM(shares_count), 0) as total_shares,
            COALESCE(SUM(total_engagement), 0) as total_engagement,
            COALESCE(SUM(pes), 0) as total_pes,
            COUNT(*) as total_posts
        FROM posts
        WHERE reactions_total > 0 OR comments_count > 0 OR shares_count > 0
    """)
    row = cursor.fetchone()

    cursor.execute("""
        SELECT MIN(publish_time), MAX(publish_time)
        FROM posts WHERE publish_time IS NOT NULL
    """)
    dates = cursor.fetchone()

    cursor.execute("SELECT COUNT(DISTINCT page_id) FROM posts WHERE reactions_total > 0")
    active_pages = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM pages")
    total_pages_count = cursor.fetchone()[0]

    post_count = row[5]
    total_engagement = row[3]
    total_pes = row[4]

    all_stats = {
        "total_posts": post_count,
        "total_pages": active_pages,
        "all_pages": total_pages_count,
        "total_reactions": row[0],
        "total_comments": row[1],
        "total_shares": row[2],
        "total_engagement": total_engagement,
        "total_pes": round(total_pes, 1),
        "avg_engagement": round(total_engagement / post_count, 1) if post_count > 0 else 0,
        "avg_pes": round(total_pes / post_count, 1) if post_count > 0 else 0,
        "date_range_start": str(dates[0])[:10] if dates[0] else None,
        "date_range_end": str(dates[1])[:10] if dates[1] else None,
    }

    # Per-page stats
    by_page = {}
    for page_id in page_ids:
        cursor.execute("""
            SELECT
                COALESCE(SUM(reactions_total), 0) as total_reactions,
                COALESCE(SUM(comments_count), 0) as total_comments,
                COALESCE(SUM(shares_count), 0) as total_shares,
                COALESCE(SUM(total_engagement), 0) as total_engagement,
                COALESCE(SUM(pes), 0) as total_pes,
                COUNT(*) as total_posts
            FROM posts
            WHERE page_id = ? AND (reactions_total > 0 OR comments_count > 0 OR shares_count > 0)
        """, (page_id,))
        prow = cursor.fetchone()

        cursor.execute("""
            SELECT MIN(publish_time), MAX(publish_time)
            FROM posts WHERE page_id = ? AND publish_time IS NOT NULL
        """, (page_id,))
        pdates = cursor.fetchone()

        ppost_count = prow[5]
        ptotal_engagement = prow[3]
        ptotal_pes = prow[4]

        by_page[page_id] = {
            "total_posts": ppost_count,
            "total_pages": 1,
            "all_pages": 1,
            "total_reactions": prow[0],
            "total_comments": prow[1],
            "total_shares": prow[2],
            "total_engagement": ptotal_engagement,
            "total_pes": round(ptotal_pes, 1),
            "avg_engagement": round(ptotal_engagement / ppost_count, 1) if ppost_count > 0 else 0,
            "avg_pes": round(ptotal_pes / ppost_count, 1) if ppost_count > 0 else 0,
            "date_range_start": str(pdates[0])[:10] if pdates[0] else None,
            "date_range_end": str(pdates[1])[:10] if pdates[1] else None,
        }

    conn.close()
    return {"all": all_stats, "byPage": by_page}


def export_pages():
    """Export page comparison data."""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            pg.page_id,
            pg.page_name,
            pg.fan_count,
            pg.followers_count,
            COUNT(p.post_id) as post_count,
            COALESCE(SUM(p.reactions_total), 0) as total_reactions,
            COALESCE(SUM(p.comments_count), 0) as total_comments,
            COALESCE(SUM(p.shares_count), 0) as total_shares,
            COALESCE(SUM(p.total_engagement), 0) as total_engagement,
            COALESCE(AVG(p.pes), 0) as avg_pes
        FROM pages pg
        LEFT JOIN posts p ON pg.page_id = p.page_id
            AND (p.reactions_total > 0 OR p.comments_count > 0 OR p.shares_count > 0)
        GROUP BY pg.page_id
        HAVING COUNT(p.post_id) > 0
        ORDER BY total_engagement DESC
    """)

    result = []
    for row in cursor.fetchall():
        post_count = row[4]
        total_engagement = row[8]
        result.append({
            "page_id": row[0],
            "page_name": row[1],
            "fan_count": row[2],
            "followers_count": row[3],
            "post_count": post_count,
            "total_reactions": row[5],
            "total_comments": row[6],
            "total_shares": row[7],
            "total_engagement": total_engagement,
            "avg_engagement": round(total_engagement / post_count, 1) if post_count > 0 else 0,
            "avg_pes": round(row[9], 1)
        })

    conn.close()
    return result


def export_post_types():
    """Export post type statistics (all pages + per-page)."""
    conn = get_conn()
    cursor = conn.cursor()

    # Get all pages first
    cursor.execute("SELECT DISTINCT page_id FROM posts WHERE reactions_total > 0")
    page_ids = [row[0] for row in cursor.fetchall()]

    # Aggregate post types
    cursor.execute("""
        SELECT
            COALESCE(post_type, 'Unknown') as post_type,
            COUNT(*) as count,
            COALESCE(SUM(reactions_total), 0) as reactions,
            COALESCE(SUM(comments_count), 0) as comments,
            COALESCE(SUM(shares_count), 0) as shares,
            COALESCE(SUM(total_engagement), 0) as total_engagement,
            COALESCE(AVG(pes), 0) as avg_pes
        FROM posts
        WHERE reactions_total > 0 OR comments_count > 0 OR shares_count > 0
        GROUP BY post_type
        ORDER BY count DESC
    """)

    all_types = []
    for row in cursor.fetchall():
        count = row[1]
        total_engagement = row[5]
        all_types.append({
            "post_type": row[0],
            "count": count,
            "reactions": row[2],
            "comments": row[3],
            "shares": row[4],
            "total_engagement": total_engagement,
            "avg_engagement": round(total_engagement / count, 1) if count > 0 else 0,
            "avg_pes": round(row[6], 1)
        })

    # Per-page post types
    by_page = {}
    for page_id in page_ids:
        cursor.execute("""
            SELECT
                COALESCE(post_type, 'Unknown') as post_type,
                COUNT(*) as count,
                COALESCE(SUM(reactions_total), 0) as reactions,
                COALESCE(SUM(comments_count), 0) as comments,
                COALESCE(SUM(shares_count), 0) as shares,
                COALESCE(SUM(total_engagement), 0) as total_engagement,
                COALESCE(AVG(pes), 0) as avg_pes
            FROM posts
            WHERE page_id = ? AND (reactions_total > 0 OR comments_count > 0 OR shares_count > 0)
            GROUP BY post_type
            ORDER BY count DESC
        """, (page_id,))

        page_types = []
        for row in cursor.fetchall():
            count = row[1]
            total_engagement = row[5]
            page_types.append({
                "post_type": row[0],
                "count": count,
                "reactions": row[2],
                "comments": row[3],
                "shares": row[4],
                "total_engagement": total_engagement,
                "avg_engagement": round(total_engagement / count, 1) if count > 0 else 0,
                "avg_pes": round(row[6], 1)
            })
        by_page[page_id] = page_types

    conn.close()
    return {"all": all_types, "byPage": by_page}


def export_daily():
    """Export daily engagement data (all pages + per-page)."""
    conn = get_conn()
    cursor = conn.cursor()

    # Get all pages first
    cursor.execute("SELECT DISTINCT page_id FROM posts WHERE reactions_total > 0")
    page_ids = [row[0] for row in cursor.fetchall()]

    # Aggregate daily data
    cursor.execute("""
        SELECT
            DATE(publish_time) as post_date,
            COUNT(*) as post_count,
            COALESCE(SUM(reactions_total), 0) as reactions,
            COALESCE(SUM(comments_count), 0) as comments,
            COALESCE(SUM(shares_count), 0) as shares,
            COALESCE(SUM(total_engagement), 0) as engagement,
            COALESCE(SUM(pes), 0) as pes
        FROM posts
        WHERE publish_time IS NOT NULL
            AND (reactions_total > 0 OR comments_count > 0 OR shares_count > 0)
        GROUP BY DATE(publish_time)
        ORDER BY post_date
    """)

    all_daily = []
    for row in cursor.fetchall():
        all_daily.append({
            "date": row[0],
            "posts": row[1],
            "reactions": row[2],
            "comments": row[3],
            "shares": row[4],
            "engagement": row[5],
            "pes": round(row[6], 1)
        })

    # Per-page daily data
    by_page = {}
    for page_id in page_ids:
        cursor.execute("""
            SELECT
                DATE(publish_time) as post_date,
                COUNT(*) as post_count,
                COALESCE(SUM(reactions_total), 0) as reactions,
                COALESCE(SUM(comments_count), 0) as comments,
                COALESCE(SUM(shares_count), 0) as shares,
                COALESCE(SUM(total_engagement), 0) as engagement,
                COALESCE(SUM(pes), 0) as pes
            FROM posts
            WHERE page_id = ? AND publish_time IS NOT NULL
                AND (reactions_total > 0 OR comments_count > 0 OR shares_count > 0)
            GROUP BY DATE(publish_time)
            ORDER BY post_date
        """, (page_id,))

        page_daily = []
        for row in cursor.fetchall():
            page_daily.append({
                "date": row[0],
                "posts": row[1],
                "reactions": row[2],
                "comments": row[3],
                "shares": row[4],
                "engagement": row[5],
                "pes": round(row[6], 1)
            })
        by_page[page_id] = page_daily

    conn.close()
    return {"all": all_daily, "byPage": by_page}


def export_top_posts(limit=10):
    """Export top performing posts (all pages + per-page)."""
    conn = get_conn()
    cursor = conn.cursor()

    # Get all pages first
    cursor.execute("SELECT DISTINCT page_id FROM posts WHERE reactions_total > 0")
    page_ids = [row[0] for row in cursor.fetchall()]

    # All pages top posts
    cursor.execute(f"""
        SELECT
            p.post_id,
            p.page_id,
            pg.page_name,
            p.title,
            p.post_type,
            p.publish_time,
            p.permalink,
            COALESCE(p.reactions_total, 0) as reactions,
            COALESCE(p.comments_count, 0) as comments,
            COALESCE(p.shares_count, 0) as shares,
            COALESCE(p.total_engagement, 0) as engagement,
            COALESCE(p.pes, 0) as pes
        FROM posts p
        LEFT JOIN pages pg ON p.page_id = pg.page_id
        WHERE p.reactions_total > 0 OR p.comments_count > 0 OR p.shares_count > 0
        ORDER BY p.total_engagement DESC
        LIMIT {limit}
    """)

    all_posts = []
    for row in cursor.fetchall():
        all_posts.append({
            "post_id": row[0],
            "page_id": row[1],
            "page_name": row[2],
            "title": row[3],
            "post_type": row[4],
            "publish_time": row[5],
            "permalink": row[6],
            "reactions": row[7],
            "comments": row[8],
            "shares": row[9],
            "engagement": row[10],
            "pes": round(row[11], 1)
        })

    # Per-page top posts
    by_page = {}
    for page_id in page_ids:
        cursor.execute(f"""
            SELECT
                p.post_id,
                p.page_id,
                pg.page_name,
                p.title,
                p.post_type,
                p.publish_time,
                p.permalink,
                COALESCE(p.reactions_total, 0) as reactions,
                COALESCE(p.comments_count, 0) as comments,
                COALESCE(p.shares_count, 0) as shares,
                COALESCE(p.total_engagement, 0) as engagement,
                COALESCE(p.pes, 0) as pes
            FROM posts p
            LEFT JOIN pages pg ON p.page_id = pg.page_id
            WHERE p.page_id = ? AND (p.reactions_total > 0 OR p.comments_count > 0 OR p.shares_count > 0)
            ORDER BY p.total_engagement DESC
            LIMIT {limit}
        """, (page_id,))

        page_posts = []
        for row in cursor.fetchall():
            page_posts.append({
                "post_id": row[0],
                "page_id": row[1],
                "page_name": row[2],
                "title": row[3],
                "post_type": row[4],
                "publish_time": row[5],
                "permalink": row[6],
                "reactions": row[7],
                "comments": row[8],
                "shares": row[9],
                "engagement": row[10],
                "pes": round(row[11], 1)
            })
        by_page[page_id] = page_posts

    conn.close()
    return {"all": all_posts, "byPage": by_page}


def main():
    print("=" * 60)
    print("Exporting Static Data for Vercel")
    print("=" * 60)

    stats_data = export_stats()
    pages_data = export_pages()
    post_types_data = export_post_types()
    daily_data = export_daily()
    top_posts_data = export_top_posts(10)

    data = {
        "stats": stats_data,
        "pages": pages_data,
        "postTypes": post_types_data,
        "daily": daily_data,
        "topPosts": top_posts_data
    }

    # Pretty print summary
    all_stats = stats_data["all"]
    print(f"\nStats:")
    print(f"  Posts: {all_stats['total_posts']}")
    print(f"  Pages: {all_stats['total_pages']}")
    print(f"  Date range: {all_stats['date_range_start']} to {all_stats['date_range_end']}")
    print(f"  Total Engagement: {all_stats['total_engagement']:,}")

    print(f"\nPages: {len(pages_data)}")
    for page in pages_data:
        print(f"  - {page['page_name']}: {page['post_count']} posts, {page['total_engagement']:,} engagement")

    print(f"\nPost Types: {len(post_types_data['all'])}")
    print(f"Daily Data Points: {len(daily_data['all'])}")
    print(f"Top Posts: {len(top_posts_data['all'])}")
    print(f"Per-page data: {len(stats_data['byPage'])} pages")

    # Save to file
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\n[OK] Exported to: {OUTPUT_PATH}")
    print("\nTo update Vercel:")
    print("  git add frontend/public/data/analytics.json")
    print("  git commit -m 'Update analytics data'")
    print("  git push")


if __name__ == "__main__":
    main()
