# Yahoo Finance provider with robust symbol mapping and fallback attempts
import yfinance as yf
import pandas as pd
from typing import Optional, List
from .. import config
import os
import time


# ----------------------------
# SYMBOL SANITIZATION HELPERS
# ----------------------------
BAD_CHARS = ['"', "'", "{", "}", ":", ",", "[", "]", "\\"]

def _sanitize_symbol(sym: str) -> Optional[str]:
    if not sym or not isinstance(sym, str):
        return None
    s = sym.strip()
    if not s:
        return None
    if any(c in s for c in BAD_CHARS):
        return None
    if " " in s:
        return None
    return s.upper()


# Primary mapping for commonly used broker-style symbols -> Yahoo tickers
PRIMARY_MAPPING = {
    "XAUUSD": ["GC=F", "GLD"],
    "XAGUSD": ["SI=F", "SLV"],
    "USOIL": ["CL=F", "USO"],
    "UKOIL": ["BZ=F"],
    "NAS100": ["QQQ", "^IXIC"],
    "US30": ["^DJI", "DIA"],
    "GER40": ["^GDAXI"],
    "US500": ["^GSPC", "SPY"],
    "SPY": ["SPY"],
    "AAPL": ["AAPL"], "MSFT": ["MSFT"], "AMZN": ["AMZN"],
    "NVDA": ["NVDA"], "TSLA": ["TSLA"], "GOOGL": ["GOOGL"],
}


# Helper: generate candidate Yahoo tickers for a given generic name
def candidates_for_symbol(sym: str) -> List[str]:
    s = _sanitize_symbol(sym)
    if not s:
        return []

    key = s.replace(" ", "")

    # mapped candidates first
    if key in PRIMARY_MAPPING:
        return PRIMARY_MAPPING[key]

    # Forex pairs like EURUSD -> EURUSD=X
    if len(key) == 6 and key.isalpha():
        return [f"{key[:3]}{key[3:]}=X", key]

    # If symbol already looks like a Yahoo ticker
    if "=" in key or "^" in key or "." in key or (key.isupper() and len(key) <= 5):
        return [key]

    # Fallback: try raw + uppercase
    return [key]


INTERVAL_MAP = {
    "4h": "4h",
    "2h": "2h",
    "15m": "15m",
    "5m": "5m"
}


# Try to download a dataframe for the first viable candidate ticker
def fetch_ohlcv(symbol: str, timeframe: str, period: str = "45d") -> Optional[pd.DataFrame]:
    interval = INTERVAL_MAP.get(timeframe, timeframe)
    cand_list = candidates_for_symbol(symbol)

    if not cand_list:
        return None

    last_err = None

    for cand in cand_list:
        try:
            for _ in range(2):
                df = yf.download(
                    cand,
                    period=period,
                    interval=interval,
                    progress=False
                )
                if df is not None and not df.empty:
                    if isinstance(df.index, pd.DatetimeIndex):
                        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
                        df.index = pd.to_datetime(df.index)
                        return df
                time.sleep(0.5)
            last_err = f"No data for candidate {cand}"
        except Exception as e:
            last_err = repr(e)
            continue

    print(
        f"yfinance: no price data for symbol '{symbol}' "
        f"using candidates {cand_list}. Last error: {last_err}"
    )
    return None


def list_symbols() -> List[str]:
    """
    Return a symbol list to seed the scanner.
    SYMBOLS_FILE (if present) takes priority.
    """
    symbols: List[str] = []

    # 1) File-based symbols
    if config.SYMBOLS_FILE and os.path.exists(config.SYMBOLS_FILE):
        with open(config.SYMBOLS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                s = _sanitize_symbol(raw)
                if s:
                    symbols.append(s)

    # 2) Defaults if file not present or empty
    if not symbols:
        defaults = [
            "XAUUSD", "XAGUSD",
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "NZDUSD",
            "EURJPY", "GBPJPY", "NZDJPY", "GBPAUD", "EURAUD",
            "GER40", "NAS100", "US30", "US500",
            "USOIL", "UKOIL",
            "AAPL", "MSFT", "AMZN", "NVDA", "TSLA", "GOOGL",
        ]
        symbols = defaults

    if config.SYMBOLS_MAX and config.SYMBOLS_MAX > 0:
        return symbols[:config.SYMBOLS_MAX]

    return symbols
