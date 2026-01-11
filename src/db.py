# SQLite persistence layer: signals and symbol table (no admin endpoints in system)
import sqlite3
from typing import Optional, Dict, List
from . import config

DB = config.DB_PATH

CREATE_STATEMENTS = [
"""
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
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, bos_ts)
);
""",
"""
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    source TEXT DEFAULT 'auto',
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""
]

def get_conn():
    conn = sqlite3.connect(DB, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    for stmt in CREATE_STATEMENTS:
        cur.execute(stmt)
    conn.commit()
    conn.close()

# Signals helpers
def insert_signal(signal: dict) -> bool:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO signals (symbol,bos_ts,direction,entry,stop,tp1,tp2,tp3,atr,pulled_back)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                signal["symbol"], signal["bos_ts"], signal["direction"],
                signal.get("entry"), signal.get("stop"), signal.get("tp1"), signal.get("tp2"), signal.get("tp3"),
                signal.get("atr", 0.0), int(signal.get("pulled_back", 0))
            )
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_signal(symbol: str, bos_ts: str) -> Optional[Dict]:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM signals WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    row = cur.fetchone(); conn.close()
    return dict(row) if row else None

def mark_bos_sent(symbol: str, bos_ts: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE signals SET notified_bos=1 WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    conn.commit(); conn.close()

def mark_market_sent(symbol: str, bos_ts: str):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE signals SET notified_market=1 WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    conn.commit(); conn.close()

def mark_notified_channel(symbol: str, bos_ts: str, channel: str):
    conn = get_conn(); cur = conn.cursor()
    col = "notified_telegram" if channel == "telegram" else "notified_whatsapp"
    cur.execute(f"UPDATE signals SET {col}=1 WHERE symbol=? AND bos_ts=?", (symbol, bos_ts))
    conn.commit(); conn.close()

def update_pulled_back(symbol: str, bos_ts: str, pulled: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE signals SET pulled_back=? WHERE symbol=? AND bos_ts=?", (int(pulled), symbol, bos_ts))
    conn.commit(); conn.close()

# Symbol table helpers
def list_symbols(enabled_only: bool = True) -> List[str]:
    conn = get_conn(); cur = conn.cursor()
    if enabled_only:
        cur.execute("SELECT symbol FROM symbols WHERE enabled=1 ORDER BY symbol")
    else:
        cur.execute("SELECT symbol FROM symbols ORDER BY symbol")
    rows = cur.fetchall(); conn.close()
    return [r["symbol"] for r in rows]

def add_symbol(symbol: str, source: str = "auto") -> bool:
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("INSERT OR IGNORE INTO symbols (symbol, source, enabled) VALUES (?,?,1)", (symbol, source))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()

# New: simple stats helper for heartbeat
def get_stats(min_rr_alert: float = 0.0) -> dict:
    conn = get_conn(); cur = conn.cursor()
    # total signals
    cur.execute("SELECT COUNT(*) as c FROM signals")
    total = cur.fetchone()["c"]
    # signals which are notified_market
    cur.execute("SELECT COUNT(*) as c FROM signals WHERE notified_market=1")
    market_sent = cur.fetchone()["c"]
    # count signals with tp2/rr >= min_rr_alert - we store rr in tp2 relative positions not explicitly,
    # but rr is stored in 'tp2' relative to entry? (legacy) -> We'll check using tp2 and stop if both set.
    # For safety, we will treat any signal with tp2 and stop as candidate for alert; more precise rr calc can be added later.
    cur.execute("SELECT COUNT(*) as c FROM signals WHERE tp2 IS NOT NULL AND stop IS NOT NULL")
    candidates = cur.fetchone()["c"]
    conn.close()
    return {"total_signals": total, "market_sent": market_sent, "candidates": candidates}