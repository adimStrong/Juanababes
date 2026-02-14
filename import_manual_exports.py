#!/usr/bin/env python3
"""Import manually exported CSV files from Meta Business Suite.

IMPORTANT: Meta CSV exports Post IDs and Page IDs in scientific notation
(e.g. 1.22187E+17, 6.15804E+13) which causes precision loss.

Strategy: IGNORE CSV Post ID entirely. Match CSV rows to existing DB posts
by (page_name + publish_time). Only UPDATE views/reach on matched posts.
API is the source of truth for post identity.
"""

import csv
import sqlite3
import os
import hashlib
from datetime import datetime, timedelta
from glob import glob

DATABASE_PATH = "data/juanbabes_analytics.db"
EXPORTS_FOLDER = "exports/from content manual Export"


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def parse_datetime_with_offset(dt_str):
    """Parse CSV datetime and add 8h offset to match DB times.

    CSV times are UTC. DB (from API) stores PHT (UTC+8) labeled as +0000.
    CSV_time + 8h = DB_time.
    """
    if not dt_str:
        return None
    try:
        dt = datetime.strptime(dt_str.strip(), "%m/%d/%Y %H:%M")
        dt_adjusted = dt + timedelta(hours=8)
        return dt_adjusted.isoformat()
    except:
        return dt_str


def safe_int(val):
    """Safely convert to int."""
    if not val or val == "":
        return 0
    try:
        return int(float(val))
    except:
        return 0


def import_csv(filepath):
    """Import a single CSV file by matching to existing DB posts."""
    print(f"\nImporting: {os.path.basename(filepath)}")

    conn = get_conn()
    cursor = conn.cursor()

    updated = 0
    created = 0
    skipped = 0

    # Build page_name -> page_id lookup from DB
    cursor.execute("SELECT page_id, page_name FROM pages")
    page_lookup = {}
    for row in cursor.fetchall():
        page_lookup[row['page_name'].lower()] = row['page_id']

    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            page_name = row.get("Page name", "")
            post_id_raw = row.get("Post ID", "")

            if not post_id_raw or not page_name:
                skipped += 1
                continue

            # Resolve page_id by name (avoids E+ page_id issue)
            page_id = page_lookup.get(page_name.lower())
            if not page_id:
                # Try partial match (strip spaces for fuzzy compare)
                csv_stripped = page_name.lower().replace(" ", "")
                for name, pid in page_lookup.items():
                    db_stripped = name.replace(" ", "")
                    if csv_stripped in db_stripped or db_stripped in csv_stripped:
                        page_id = pid
                        break
            if not page_id:
                skipped += 1
                continue

            # Parse time with +8h offset
            publish_time = parse_datetime_with_offset(row.get("Publish time", ""))
            if not publish_time:
                skipped += 1
                continue

            views = safe_int(row.get("Views", 0))
            reach = safe_int(row.get("Reach", 0))
            reactions = safe_int(row.get("Reactions", 0))
            comments = safe_int(row.get("Comments", 0))
            shares = safe_int(row.get("Shares", 0))

            # Match by page_id + publish_time (truncated to minute)
            time_prefix = publish_time[:16] if publish_time else ""
            title = (row.get("Title", "") or "")[:100].strip()

            cursor.execute("""
                SELECT post_id FROM posts
                WHERE page_id = ? AND SUBSTR(publish_time, 1, 16) = ?
                LIMIT 1
            """, (page_id, time_prefix))
            match = cursor.fetchone()

            # Fallback: fuzzy time match (+/-10 minutes)
            if not match:
                from datetime import datetime as dt2
                try:
                    base = dt2.fromisoformat(publish_time)
                    for offset_min in [-1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7, -8, 8, -9, 9, -10, 10]:
                        tp = (base + timedelta(minutes=offset_min)).isoformat()[:16]
                        cursor.execute("""
                            SELECT post_id FROM posts
                            WHERE page_id = ? AND SUBSTR(publish_time, 1, 16) = ?
                            LIMIT 1
                        """, (page_id, tp))
                        match = cursor.fetchone()
                        if match:
                            break
                except:
                    pass

            # Fallback: match by title on same date (for midnight-timestamp posts)
            if not match and title:
                date_part = publish_time[:10] if publish_time else ""
                cursor.execute("""
                    SELECT post_id FROM posts
                    WHERE page_id = ? AND SUBSTR(publish_time, 1, 10) = ?
                    AND LOWER(SUBSTR(title, 1, 100)) = LOWER(?)
                    LIMIT 1
                """, (page_id, date_part, title))
                match = cursor.fetchone()

            # Fallback: match by title on ANY date (midnight posts may be off by a day)
            if not match and title and len(title) > 20:
                cursor.execute("""
                    SELECT post_id FROM posts
                    WHERE page_id = ? AND LOWER(SUBSTR(title, 1, 100)) = LOWER(?)
                    LIMIT 1
                """, (page_id, title))
                match = cursor.fetchone()

            # Fallback: closest time match on same date (within 60 min window)
            if not match:
                from datetime import datetime as dt2
                try:
                    base = dt2.fromisoformat(publish_time)
                    date_part = publish_time[:10]
                    cursor.execute("""
                        SELECT post_id, publish_time FROM posts
                        WHERE page_id = ? AND SUBSTR(publish_time, 1, 10) = ?
                        AND post_id NOT IN (
                            SELECT post_id FROM posts
                            WHERE views_count > 0
                        )
                    """, (page_id, date_part))
                    candidates = cursor.fetchall()
                    best_match = None
                    best_diff = 3600  # 60 min max
                    for cand in candidates:
                        try:
                            cand_time = dt2.fromisoformat(cand['publish_time'].replace('+0000', ''))
                            diff = abs((cand_time - base).total_seconds())
                            if diff < best_diff:
                                best_diff = diff
                                best_match = cand
                        except:
                            pass
                    if best_match:
                        match = best_match
                except:
                    pass

            if match:
                matched_post_id = match['post_id']
                total_engagement = reactions + comments + shares
                pes = (reactions * 1.0) + (comments * 2.0) + (shares * 3.0)

                cursor.execute("""
                    UPDATE posts SET
                        views_count = MAX(COALESCE(views_count, 0), ?),
                        reach_count = MAX(COALESCE(reach_count, 0), ?),
                        reactions_total = MAX(COALESCE(reactions_total, 0), ?),
                        comments_count = MAX(COALESCE(comments_count, 0), ?),
                        shares_count = MAX(COALESCE(shares_count, 0), ?),
                        total_engagement = MAX(COALESCE(total_engagement, 0), ?),
                        pes = MAX(COALESCE(pes, 0), ?)
                    WHERE post_id = ?
                """, (views, reach, reactions, comments, shares,
                      total_engagement, pes, matched_post_id))
                updated += 1
            else:
                # CREATE post from CSV data (for posts API can't reach)
                # Generate deterministic post ID from page_id + publish_time
                id_seed = f"{page_id}_{publish_time}"
                synthetic_id = f"csv_{hashlib.md5(id_seed.encode()).hexdigest()[:12]}"

                # Check if this synthetic ID already exists
                cursor.execute("SELECT post_id FROM posts WHERE post_id = ?", (synthetic_id,))
                if cursor.fetchone():
                    # Already inserted from a previous CSV import run
                    updated += 1
                    cursor.execute("""
                        UPDATE posts SET
                            views_count = MAX(COALESCE(views_count, 0), ?),
                            reach_count = MAX(COALESCE(reach_count, 0), ?),
                            reactions_total = MAX(COALESCE(reactions_total, 0), ?),
                            comments_count = MAX(COALESCE(comments_count, 0), ?),
                            shares_count = MAX(COALESCE(shares_count, 0), ?),
                            total_engagement = MAX(COALESCE(total_engagement, 0), ?),
                            pes = MAX(COALESCE(pes, 0), ?)
                        WHERE post_id = ?
                    """, (views, reach, reactions, comments, shares,
                          reactions + comments + shares,
                          (reactions * 1.0) + (comments * 2.0) + (shares * 3.0),
                          synthetic_id))
                else:
                    total_engagement = reactions + comments + shares
                    pes = (reactions * 1.0) + (comments * 2.0) + (shares * 3.0)
                    post_type = row.get("Type", "Videos")
                    cursor.execute("""
                        INSERT INTO posts
                        (post_id, page_id, title, post_type, publish_time,
                         views_count, reach_count,
                         reactions_total, comments_count, shares_count,
                         total_engagement, pes, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        synthetic_id, page_id, title, post_type,
                        publish_time + "+0000" if "+0000" not in publish_time else publish_time,
                        views, reach, reactions, comments, shares,
                        total_engagement, pes, datetime.now().isoformat()
                    ))
                    created += 1

    conn.commit()
    conn.close()

    print(f"  Updated {updated} posts with views/reach data")
    if created > 0:
        print(f"  Created {created} new posts from CSV (not in API)")
    if skipped > 0:
        print(f"  {skipped} rows skipped (missing data)")
    return updated + created


def main():
    print("=" * 60)
    print("Importing Manual CSV Exports (views/reach update only)")
    print("=" * 60)

    csv_files = glob(os.path.join(EXPORTS_FOLDER, "*.csv"))

    if not csv_files:
        print(f"No CSV files found in {EXPORTS_FOLDER}")
        return

    print(f"Found {len(csv_files)} CSV files")

    total_updated = 0
    for csv_file in sorted(csv_files):
        count = import_csv(csv_file)
        total_updated += count

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total posts updated: {total_updated}")

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.page_name, COUNT(po.post_id) as post_count,
               SUM(po.reactions_total) as total_reactions,
               SUM(po.views_count) as total_views,
               SUM(po.reach_count) as total_reach
        FROM pages p
        LEFT JOIN posts po ON p.page_id = po.page_id
        GROUP BY p.page_id
        ORDER BY post_count DESC
    """)

    print("\nPage breakdown:")
    for row in cursor.fetchall():
        print(f"  {row['page_name']}: {row['post_count']} posts, "
              f"{row['total_reactions'] or 0} reactions, {row['total_views'] or 0} views")

    conn.close()


if __name__ == "__main__":
    main()
