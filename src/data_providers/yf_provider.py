# Yahoo Finance provider for testing / backfill
import yfinance as yf
import pandas as pd
from typing import Optional

INTERVAL_MAP = {
    "4h": "4h",
    "2h": "2h",
    "15m": "15m",
    "5m": "5m"
}

def fetch_ohlcv(symbol: str, timeframe: str, period: str = "45d") -> Optional[pd.DataFrame]:
    # timeframe must be one of INTERVAL_MAP keys
    interval = INTERVAL_MAP.get(timeframe, timeframe)
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    if df is None or df.empty:
        return None
    df = df[['Open','High','Low','Close','Volume']].copy()
    df.index = pd.to_datetime(df.index)
    return df