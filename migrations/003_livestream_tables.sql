-- Livestream analytics tables (TikTok + Bigo)
-- Source: Google Sheet 1OIrB1Sco1ieFFsJQcviQFyPob3evq3PO2MAtRFfyeJ4

CREATE TABLE IF NOT EXISTS livestream_daily (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    agent TEXT NOT NULL,
    -- TikTok
    tk_views INTEGER DEFAULT 0,
    tk_unique_viewers INTEGER DEFAULT 0,
    tk_likes INTEGER DEFAULT 0,
    tk_comments INTEGER DEFAULT 0,
    tk_shares INTEGER DEFAULT 0,
    tk_gifters INTEGER DEFAULT 0,
    tk_new_followers INTEGER DEFAULT 0,
    tk_eng_rate REAL DEFAULT 0,
    -- Bigo
    bg_viewers INTEGER DEFAULT 0,
    bg_engaged INTEGER DEFAULT 0,
    bg_eng_rate REAL DEFAULT 0,
    bg_beans REAL DEFAULT 0,
    bg_new_fans INTEGER DEFAULT 0,
    bg_gifts INTEGER DEFAULT 0,
    -- Computed
    total_engagement INTEGER DEFAULT 0,
    total_reach INTEGER DEFAULT 0,
    -- Meta
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, agent)
);

CREATE TABLE IF NOT EXISTS livestream_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    streamer TEXT,
    platform TEXT,
    content TEXT,
    other_task TEXT,
    moderator TEXT,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS livestream_promo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent TEXT NOT NULL,
    code TEXT NOT NULL,
    status TEXT DEFAULT 'UNUSED',
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(agent, code)
);
