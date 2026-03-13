#!/usr/bin/env python3
"""
Fetch livestream data (TikTok + Bigo) from Google Sheet into SQLite.

Source: Google Sheet 1OIrB1Sco1ieFFsJQcviQFyPob3evq3PO2MAtRFfyeJ4
Service Account: bd-bot-ni-adim@gen-lang-client-0641615854.iam.gserviceaccount.com

Usage:
    python fetch_livestream.py
"""

import os
import sys
import time
import sqlite3
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

# ── Config ──
SHEET_ID = "1OIrB1Sco1ieFFsJQcviQFyPob3evq3PO2MAtRFfyeJ4"
CRED_FILE = r"C:\Users\us\Downloads\gen-lang-client-0641615854-3f3da77cdc2b.json"
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "juanbabes_analytics.db")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

AGENTS = ["SENA", "ASHLEY", "ABI", "JAM"]
AGENT_TABS = {
    "SENA": "SENA- BIGOTIKTOK DATA",
    "ASHLEY": "ASHLEY- BIGOTIKTOK DATA",
    "ABI": "ABI - BIGOTIKTOK DATA",
    "JAM": "JAM - BIGOTIKTOK DATA",
}

# TikTok columns (A-J = 0-9)
TK = {"date": 0, "views": 1, "unique": 2, "likes": 3, "comments": 4,
      "shares": 5, "gifters": 6, "new_followers": 7, "eng_rate": 8}

# Bigo columns (K-R = 10-17)
BG = {"date": 10, "viewers": 11, "engaged": 12, "eng_rate": 13,
      "beans": 14, "gifts": 15, "new_fans": 16}

HEADER_ROW = 2  # 0-based index of header row in agent tabs

TAB_SCHEDULE = "SCHEDULE"
TAB_PROMO = "PROMO CODE LIST"

PROMO_AGENTS = {
    "SENA": {"code": 0, "status": 1},
    "ASHLEY": {"code": 3, "status": 4},
    "ABI": {"code": 6, "status": 7},
    "JAM": {"code": 9, "status": 10},
}


# ── Helpers ──

def pf(val):
    if not val or not str(val).strip():
        return 0.0
    s = str(val).strip().replace(",", "").replace("%", "")
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0

def pi(val):
    return int(pf(val))

def parse_date(val):
    if not val or not str(val).strip():
        return None
    s = str(val).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y", "%m/%d"):
        try:
            d = datetime.strptime(s, fmt)
            if d.year == 1900:
                d = d.replace(year=datetime.now().year)
            return d.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def get_client():
    creds = Credentials.from_service_account_file(CRED_FILE, scopes=SCOPES)
    return gspread.authorize(creds)


def init_db(conn):
    """Run migration to create livestream tables if needed."""
    migration_path = os.path.join(os.path.dirname(__file__), "migrations", "003_livestream_tables.sql")
    with open(migration_path) as f:
        conn.executescript(f.read())
    conn.commit()


# ── Sync Functions ──

def sync_agent_data(client, sh, conn):
    """Sync TikTok + Bigo daily data for all agents."""
    total = 0
    for agent in AGENTS:
        tab_name = AGENT_TABS[agent]
        try:
            ws = sh.worksheet(tab_name)
            rows = ws.get_all_values()
        except Exception as e:
            print(f"  [WARN] Could not read {tab_name}: {e}")
            continue

        count = 0
        for i in range(HEADER_ROW + 1, len(rows)):
            row = rows[i]
            if len(row) < 2:
                continue

            tk_date = parse_date(row[TK["date"]] if TK["date"] < len(row) else "")
            bg_date = parse_date(row[BG["date"]] if BG["date"] < len(row) else "")
            date = tk_date or bg_date
            if not date:
                continue

            def g(col_map, key):
                idx = col_map[key]
                return row[idx] if idx < len(row) else ""

            tk_likes = pi(g(TK, "likes"))
            tk_comments = pi(g(TK, "comments"))
            tk_shares = pi(g(TK, "shares"))
            bg_engaged = pi(g(BG, "engaged"))
            tk_views = pi(g(TK, "views"))
            bg_viewers = pi(g(BG, "viewers"))

            total_eng = tk_likes + tk_comments + tk_shares + bg_engaged
            total_reach = tk_views + bg_viewers

            conn.execute("""
                INSERT INTO livestream_daily (
                    date, agent, tk_views, tk_unique_viewers, tk_likes, tk_comments,
                    tk_shares, tk_gifters, tk_new_followers, tk_eng_rate,
                    bg_viewers, bg_engaged, bg_eng_rate, bg_beans, bg_new_fans, bg_gifts,
                    total_engagement, total_reach, synced_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(date, agent) DO UPDATE SET
                    tk_views=excluded.tk_views, tk_unique_viewers=excluded.tk_unique_viewers,
                    tk_likes=excluded.tk_likes, tk_comments=excluded.tk_comments,
                    tk_shares=excluded.tk_shares, tk_gifters=excluded.tk_gifters,
                    tk_new_followers=excluded.tk_new_followers, tk_eng_rate=excluded.tk_eng_rate,
                    bg_viewers=excluded.bg_viewers, bg_engaged=excluded.bg_engaged,
                    bg_eng_rate=excluded.bg_eng_rate, bg_beans=excluded.bg_beans,
                    bg_new_fans=excluded.bg_new_fans, bg_gifts=excluded.bg_gifts,
                    total_engagement=excluded.total_engagement, total_reach=excluded.total_reach,
                    synced_at=excluded.synced_at
            """, (
                date, agent,
                tk_views, pi(g(TK, "unique")), tk_likes, tk_comments,
                tk_shares, pi(g(TK, "gifters")), pi(g(TK, "new_followers")), pf(g(TK, "eng_rate")),
                bg_viewers, bg_engaged, pf(g(BG, "eng_rate")), pf(g(BG, "beans")),
                pi(g(BG, "new_fans")), pi(g(BG, "gifts")),
                total_eng, total_reach, datetime.now().isoformat(),
            ))
            count += 1

        print(f"  {agent}: {count} daily rows")
        total += count

    conn.commit()
    return total


def sync_schedule(client, sh, conn):
    """Sync schedule tab."""
    try:
        ws = sh.worksheet(TAB_SCHEDULE)
        rows = ws.get_all_values()
    except Exception as e:
        print(f"  [WARN] Could not read schedule: {e}")
        return 0

    if not rows or len(rows) < 3:
        return 0

    conn.execute("DELETE FROM livestream_schedule")

    day_blocks = []
    for j, cell in enumerate(rows[0]):
        cell_s = cell.strip()
        if cell_s:
            d = parse_date(cell_s.split("(")[0].strip())
            day_blocks.append({"col_start": j, "date": d or cell_s})

    count = 0
    for block in day_blocks:
        cs = block["col_start"]
        date_label = block["date"]

        for i in range(2, len(rows)):
            row = rows[i]
            time_val = row[cs].strip() if cs < len(row) else ""
            if not time_val:
                continue
            streamer = row[cs + 1].strip() if cs + 1 < len(row) else ""
            platform = row[cs + 2].strip() if cs + 2 < len(row) else ""
            content = row[cs + 3].strip() if cs + 3 < len(row) else ""
            other_task = row[cs + 4].strip() if cs + 4 < len(row) else ""
            moderator = row[cs + 5].strip() if cs + 5 < len(row) else ""

            # Normalize platform
            pu = platform.upper()
            if "TIKTOK" in pu:
                platform = "TikTok"
            elif "BIGO" in pu:
                platform = "Bigo"
            elif "FB" in pu or "FACEBOOK" in pu:
                platform = "Facebook"

            conn.execute("""
                INSERT INTO livestream_schedule (date, time, streamer, platform, content, other_task, moderator)
                VALUES (?,?,?,?,?,?,?)
            """, (date_label, time_val, streamer, platform, content, other_task, moderator))
            count += 1

    conn.commit()
    return count


def sync_promo(client, sh, conn):
    """Sync promo codes tab."""
    try:
        ws = sh.worksheet(TAB_PROMO)
        rows = ws.get_all_values()
    except Exception as e:
        print(f"  [WARN] Could not read promo codes: {e}")
        return 0

    # Find header
    header_idx = 0
    for i, row in enumerate(rows):
        joined = " ".join(str(c).lower() for c in row)
        if "code" in joined or "status" in joined:
            header_idx = i
            break

    conn.execute("DELETE FROM livestream_promo")
    count = 0
    for agent, cols in PROMO_AGENTS.items():
        for i in range(header_idx + 1, len(rows)):
            row = rows[i]
            code = row[cols["code"]].strip() if cols["code"] < len(row) else ""
            status = row[cols["status"]].strip().upper() if cols["status"] < len(row) else ""
            if not code or code.upper() == "CODE":
                continue
            conn.execute("""
                INSERT INTO livestream_promo (agent, code, status)
                VALUES (?,?,?)
                ON CONFLICT(agent, code) DO UPDATE SET status=excluded.status, synced_at=CURRENT_TIMESTAMP
            """, (agent, code, status or "UNUSED"))
            count += 1

    conn.commit()
    return count


def main():
    print("=" * 60)
    print("Fetching Livestream Data (TikTok + Bigo)")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    client = get_client()
    sh = client.open_by_key(SHEET_ID)

    print("\n[1/3] Syncing agent daily data...")
    daily_count = sync_agent_data(client, sh, conn)
    print(f"  Total: {daily_count} rows synced")

    print("\n[2/3] Syncing schedule...")
    sched_count = sync_schedule(client, sh, conn)
    print(f"  {sched_count} schedule entries")

    print("\n[3/3] Syncing promo codes...")
    promo_count = sync_promo(client, sh, conn)
    print(f"  {promo_count} promo codes")

    conn.close()
    print(f"\n[OK] Livestream data synced to {DB_PATH}")


if __name__ == "__main__":
    main()
