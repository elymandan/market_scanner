# Very small SQLite persistence layer for dedupe & audit
import sqlite3
from typing import Optional, Dict
from datetime import datetime
from . import config

DB = config.DB_PATH

CREATE = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    bos_ts TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry REAL,
    stop REAL,
    tp1 REAL,
    tp2 REAL,
    tp3 REAL,
    atr REAL,
    pulled_back INTEGER DEFAULT 0,
    notified_bos INTEGER DEFAULT 0,
    notified_market INTEGER DEFAULT 0,
    notified_telegram INTEGER DEFAULT 0,
    notified_whatsapp INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_symbol_bosts ON signals(symbol, bos_ts);
"""

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    for stmt in CREATE.split(";"):
        s = stmt.strip()
        if s:
            cur.execute(s)
    conn.commit()
    conn.close()

def insert_signal(signal: dict) -> bool:
    """
    Insert new signal. Returns True if inserted. If already exists (same symbol & bos_ts) returns False.
    """
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO signals (symbol,bos_ts,direction,entry,stop,tp1,tp2,tp3,atr,pulled_back)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                signal["symbol"], signal["bos_ts"], signal["direction"],
                signal["entry"], signal["stop"], signal["tp1"], signal["tp2"], signal["tp3"],
                signal.get("atr", 0.0), int(signal.get("pulled_back", 0))
            )
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # already exists (dedupe)
        return False
    finally:
        conn.close()

def get_signal(symbol: str, bos_ts: str) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM signals WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)

def mark_bos_sent(symbol: str, bos_ts: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE signals SET notified_bos=1 WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    conn.commit()
    conn.close()

def mark_market_sent(symbol: str, bos_ts: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE signals SET notified_market=1 WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    conn.commit()
    conn.close()

def mark_notified_channel(symbol: str, bos_ts: str, channel: str):
    """
    Mark channel-specific notified flag (telegram/whatsapp).
    """
    conn = get_conn()
    cur = conn.cursor()
    col = "notified_telegram" if channel == "telegram" else "notified_whatsapp"
    cur.execute(f"UPDATE signals SET {col}=1 WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    conn.commit()
    conn.close()

def update_pulled_back(symbol: str, bos_ts: str, pulled: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE signals SET pulled_back=? WHERE symbol=? AND bos_ts=?", (int(pulled), symbol, bos_ts))
    conn.commit()
    conn.close()