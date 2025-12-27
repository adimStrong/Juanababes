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
    """Export dashboard stats."""
    conn = get_conn()
    cursor = conn.cursor()

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
    total_pages = cursor.fetchone()[0]

    conn.close()

    post_count = row[5]
    total_engagement = row[3]
    total_pes = row[4]

    return {
        "total_posts": post_count,
        "total_pages": active_pages,
        "all_pages": total_pages,
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
    """Export post type statistics."""
    conn = get_conn()
    cursor = conn.cursor()

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

    result = []
    for row in cursor.fetchall():
        count = row[1]
        total_engagement = row[5]
        result.append({
            "post_type": row[0],
            "count": count,
            "reactions": row[2],
            "comments": row[3],
            "shares": row[4],
            "total_engagement": total_engagement,
            "avg_engagement": round(total_engagement / count, 1) if count > 0 else 0,
            "avg_pes": round(row[6], 1)
        })

    conn.close()
    return result


def export_daily():
    """Export daily engagement data."""
    conn = get_conn()
    cursor = conn.cursor()

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

    result = []
    for row in cursor.fetchall():
        result.append({
            "date": row[0],
            "posts": row[1],
            "reactions": row[2],
            "comments": row[3],
            "shares": row[4],
            "engagement": row[5],
            "pes": round(row[6], 1)
        })

    conn.close()
    return result


def export_top_posts(limit=10):
    """Export top performing posts."""
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(f"""
        SELECT
            p.post_id,
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

    result = []
    for row in cursor.fetchall():
        result.append({
            "post_id": row[0],
            "page_name": row[1],
            "title": row[2],
            "post_type": row[3],
            "publish_time": row[4],
            "permalink": row[5],
            "reactions": row[6],
            "comments": row[7],
            "shares": row[8],
            "engagement": row[9],
            "pes": round(row[10], 1)
        })

    conn.close()
    return result


def main():
    print("=" * 60)
    print("Exporting Static Data for Vercel")
    print("=" * 60)

    data = {
        "stats": export_stats(),
        "pages": export_pages(),
        "postTypes": export_post_types(),
        "daily": export_daily(),
        "topPosts": export_top_posts(10)
    }

    # Pretty print summary
    print(f"\nStats:")
    print(f"  Posts: {data['stats']['total_posts']}")
    print(f"  Pages: {data['stats']['total_pages']}")
    print(f"  Date range: {data['stats']['date_range_start']} to {data['stats']['date_range_end']}")
    print(f"  Total Engagement: {data['stats']['total_engagement']:,}")

    print(f"\nPages: {len(data['pages'])}")
    for page in data['pages']:
        print(f"  - {page['page_name']}: {page['post_count']} posts, {page['total_engagement']:,} engagement")

    print(f"\nPost Types: {len(data['postTypes'])}")
    print(f"Daily Data Points: {len(data['daily'])}")
    print(f"Top Posts: {len(data['topPosts'])}")

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
