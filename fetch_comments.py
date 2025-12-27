#!/usr/bin/env python3
"""
Fetch comment data from Facebook Graph API to analyze self-comments vs organic comments.

This script:
1. Gets all posts from the database
2. Fetches comments for each post from Facebook API
3. Counts self-comments (from page) vs organic comments (from users)
4. Updates the database with the breakdown

Usage:
    python fetch_comments.py
    python fetch_comments.py --limit 50  # Test with 50 posts first
"""

import sqlite3
import requests
import time
import argparse
from datetime import datetime

DATABASE_PATH = "data/juanbabes_analytics.db"

# Page tokens from .env
PAGE_TOKENS = {
    "748765068327821": "EAAMdFdBzw7sBQSIriBg6oFVl5OjNFimTcrXoZB960BSx5xyrV4NKmepHknBErmUXlzJDRZBZBzJihVRddYEgYBlnCo7Wt18HkCweEZCv0rsQGtHUQaq7SFFUGV5cLHuwhZC7YwDgGQ8HQ8GoDhlu5QS0ydSMknRBzKH5MUVGsO4LgEHsGKgGq3VazxOlLoYz5PV71jl1PyrKRJZAhMbRhaPewt",  # Ashley
    "679225045126482": "EAAMdFdBzw7sBQaZAzzDqehFuONRDlrCQ7XPPEmfHfwgKI0EgOpN6gspIdSEC5fbinC324WbExMnpsSmSXxyEk9yHx6HLt1QM7fhl7L5rd2PePJ03siffTG0JSIaLJ79AsGEv3CGgiw6baYaEgPn5AkhYwcL4AzeEI3UTF6ssDC9wAuVMAOVZA7RXHho7EZBsoJhO58VTKsRF4OAl7UZA",  # Jam
    "580596361807116": "EAAMdFdBzw7sBQTti7nzopntIviMoA8BWisuukiiSSHt4SoB6mEc1hMgv5gCiZBpdsEI27QLqXzHYmouyEbawrvgP2Tqxtcs52UyIwoiiGtxL5cveovdbW4yFxSL1ZAVZCbPOE6CgmP0jTmZBHDEERGMJZCcGdTgjqZBBVGN8THMNYEcBoI48VqbMHtkLyl6ZAaIcIER9ZCKZAUyHJAnMk8RYxaYun",  # Abi
    "1188691322622526": "EAAMdFdBzw7sBQXVRBdhePPRhmiL7eZBpA0Jfe4A1USkU4xDsTWZCkQrsO6v4TmWwmahpZAC1MmCHDAsUnPh25MdlTQzjyjQbelzQhqyz4LigBr5bCRAPm2uVn4arJoYfsXo17x2A4NUmLRHJamtr5gi2OiRe6ntWs7gYcYf7EBH6vh8i14YZCYKZAYP3tpZCkacsQjIS9KZBFEmwBSURtbQChFB",  # Sena
    "754416584427163": "EAAMdFdBzw7sBQSBNZBnhRkjNlIoDXZAtL8XRU1bZAy2fbsZBCEHpMZCgK4kA3wGoPAXSB4B7W0irDPD6XfYgeAjkFipoH8SL2WlsNAnNW6AXvconV7WjQgfPwj0ikj1yZAVqqyQ5TZBnma67rdB1FeGBN1aVtJ3OfZCTKc91SD73ZAjZCgZCkZAf1dY1B2BZC5CPXVMAlSJ7hNXleU2PJNsfb1rdH",  # Zell
}

# Map database page_id to API page_id
# The database has different IDs (from CSV import) than the actual Facebook page IDs
PAGE_ID_MAP = {
    "61580337497087": "748765068327821",  # Ashley
    "61580395595183": "679225045126482",  # Jam
    "61580716220863": "580596361807116",  # Abi
    "61580361006776": "1188691322622526", # Sena
    "61580479407070": "754416584427163",  # Zell
}


def get_token_for_page(db_page_id):
    """Get the API token for a page based on database page_id."""
    api_page_id = PAGE_ID_MAP.get(db_page_id)
    if api_page_id:
        return PAGE_TOKENS.get(api_page_id), api_page_id
    return None, None


def fetch_comments_for_post(post_id, token, api_page_id):
    """
    Fetch comments for a post and count self-comments vs organic.

    Returns: (self_comments, organic_comments, has_page_comment)
    """
    # Facebook API expects post_id in format: {page_id}_{post_id}
    full_post_id = f"{api_page_id}_{post_id}"
    url = f"https://graph.facebook.com/v21.0/{full_post_id}/comments"
    params = {
        "fields": "from",
        "limit": 100,
        "access_token": token
    }

    self_comments = 0
    organic_comments = 0

    try:
        while url:
            response = requests.get(url, params=params)
            data = response.json()

            if "error" in data:
                # Post might be deleted or inaccessible
                return 0, 0, False

            comments = data.get("data", [])
            for comment in comments:
                commenter = comment.get("from", {})
                commenter_id = commenter.get("id", "")

                # Check if commenter is the page owner
                if commenter_id == api_page_id:
                    self_comments += 1
                else:
                    organic_comments += 1

            # Pagination
            paging = data.get("paging", {})
            url = paging.get("next")
            params = {}  # Next URL includes params

    except Exception as e:
        print(f"  Error: {e}")
        return 0, 0, False

    has_page_comment = self_comments > 0
    return self_comments, organic_comments, has_page_comment


def main():
    parser = argparse.ArgumentParser(description="Fetch comment data from Facebook API")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of posts to process (0 = all)")
    parser.add_argument("--skip-zero", action="store_true", help="Skip posts with 0 comments")
    args = parser.parse_args()

    print("=" * 60)
    print("Fetching Comment Data from Facebook API")
    print("=" * 60)

    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    # Get posts with comments
    query = """
        SELECT post_id, page_id, comments_count
        FROM posts
        WHERE comments_count > 0
        ORDER BY comments_count DESC
    """
    if args.limit > 0:
        query += f" LIMIT {args.limit}"

    cursor.execute(query)
    posts = cursor.fetchall()

    print(f"Found {len(posts)} posts with comments to process")
    print()

    processed = 0
    updated = 0
    errors = 0

    total_self = 0
    total_organic = 0

    for i, (post_id, db_page_id, comments_count) in enumerate(posts):
        token, api_page_id = get_token_for_page(db_page_id)

        if not token:
            print(f"[{i+1}/{len(posts)}] No token for page {db_page_id}, skipping")
            errors += 1
            continue

        print(f"[{i+1}/{len(posts)}] Post {post_id[:30]}... ({comments_count} comments)")

        self_comments, organic_comments, has_page_comment = fetch_comments_for_post(
            post_id, token, api_page_id
        )

        if self_comments + organic_comments > 0:
            print(f"  -> Self: {self_comments}, Organic: {organic_comments}")

            cursor.execute("""
                UPDATE posts
                SET page_comments = ?, has_page_comment = ?
                WHERE post_id = ?
            """, (self_comments, 1 if has_page_comment else 0, post_id))

            total_self += self_comments
            total_organic += organic_comments
            updated += 1
        else:
            print(f"  -> No comments found (post may be deleted)")

        processed += 1

        # Rate limiting - Facebook allows ~200 calls per hour
        time.sleep(0.5)

        # Commit every 50 posts
        if processed % 50 == 0:
            conn.commit()
            print(f"\n--- Checkpoint: {processed} posts processed ---\n")

    conn.commit()

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Posts processed: {processed}")
    print(f"Posts updated: {updated}")
    print(f"Errors: {errors}")
    print()
    print(f"Total self-comments: {total_self:,}")
    print(f"Total organic comments: {total_organic:,}")
    if total_self + total_organic > 0:
        pct = (total_self / (total_self + total_organic)) * 100
        print(f"Self-comment rate: {pct:.1f}%")

    # Show posts with most self-comments
    print()
    print("Posts with most self-comments:")
    cursor.execute("""
        SELECT p.post_id, pg.page_name, p.page_comments, p.comments_count
        FROM posts p
        LEFT JOIN pages pg ON p.page_id = pg.page_id
        WHERE p.page_comments > 0
        ORDER BY p.page_comments DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        page = row[1].replace("Juana Babe ", "") if row[1] else "Unknown"
        print(f"  {page}: {row[2]} self / {row[3]} total")

    conn.close()
    print()
    print("Done! Run 'python export_static_data.py' to update Vercel data.")


if __name__ == "__main__":
    main()
