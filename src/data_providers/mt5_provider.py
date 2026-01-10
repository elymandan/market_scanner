# MetaTrader5 provider (live). Requires MetaTrader5 terminal installed on host.
# Use PROVIDER="mt5" in config to use this.
import MetaTrader5 as mt5
import pandas as pd
import time
from typing import Optional
from datetime import datetime, timezone

TIMEFRAME_MAP = {
    "4h": mt5.TIMEFRAME_H4,
    "2h": mt5.TIMEFRAME_H2,
    "15m": mt5.TIMEFRAME_M15,
    "5m": mt5.TIMEFRAME_M5
}

def initialize(mt5_path: str = None) -> bool:
    if mt5_path:
        return mt5.initialize(path=mt5_path)
    return mt5.initialize()

def fetch_ohlcv(symbol: str, timeframe: str, count: int = 500) -> Optional[pd.DataFrame]:
    tf = TIMEFRAME_MAP.get(timeframe)
    if tf is None:
        raise ValueError("Unsupported timeframe for MT5")
    rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df = df.rename(columns={'time': 'Date', 'open':'Open','high':'High','low':'Low','close':'Close','tick_volume':'Volume'})
    df = df.set_index('Date')[['Open','High','Low','Close','Volume']]
    return df