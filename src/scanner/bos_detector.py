import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()


def find_swings(
    df: pd.DataFrame, left: int = 3, right: int = 3
) -> Tuple[List[int], List[int]]:
    highs = df["High"].values
    lows = df["Low"].values
    n = len(df)

    swing_highs: List[int] = []
    swing_lows: List[int] = []

    for i in range(left, n - right):
        window_h = highs[i - left : i + right + 1]
        window_l = lows[i - left : i + right + 1]

        if highs[i] == window_h.max() and np.sum(window_h == highs[i]) == 1:
            swing_highs.append(i)

        if lows[i] == window_l.min() and np.sum(window_l == lows[i]) == 1:
            swing_lows.append(i)

    return swing_highs, swing_lows


def detect_bos(
    df: pd.DataFrame,
    left: int = 3,
    right: int = 3,
    lookback: int = 15,
) -> Optional[Dict]:

    if len(df) < (left + right + lookback):
        return None

    swing_highs, swing_lows = find_swings(df, left, right)

    try:
        last_close = df["Close"].iloc[-1].item()
        last_open = df["Open"].iloc[-1].item()
    except (IndexError, ValueError):
        return None

    # -------------------------------------------------
    # BULLISH BOS
    # -------------------------------------------------
    if swing_highs:
        prev_high_idx = swing_highs[-1]
        prev_high_price = df["High"].iloc[prev_high_idx].item()

        search_start = max(prev_high_idx + 1, len(df) - lookback)
        recent_closes = df["Close"].iloc[search_start:]

        if not recent_closes.empty:
            breaks = recent_closes > prev_high_price

            if not breaks.empty and breaks.any().item():
                first_break_ts = breaks.idxmax()
                return {
                    "direction": "long",
                    "bos_price": prev_high_price,
                    "bos_ts": (
                        first_break_ts.isoformat()
                        if hasattr(first_break_ts, "isoformat")
                        else str(first_break_ts)
                    ),
                    "last_close": last_close,
                    "last_open": last_open,
                }

    # -------------------------------------------------
    # BEARISH BOS
    # -------------------------------------------------
    if swing_lows:
        prev_low_idx = swing_lows[-1]
        prev_low_price = df["Low"].iloc[prev_low_idx].item()

        search_start = max(prev_low_idx + 1, len(df) - lookback)
        recent_closes = df["Close"].iloc[search_start:]

        if not recent_closes.empty:
            breaks = recent_closes < prev_low_price

            if not breaks.empty and breaks.any().item():
                first_break_ts = breaks.idxmax()
                return {
                    "direction": "short",
                    "bos_price": prev_low_price,
                    "bos_ts": (
                        first_break_ts.isoformat()
                        if hasattr(first_break_ts, "isoformat")
                        else str(first_break_ts)
                    ),
                    "last_close": last_close,
                    "last_open": last_open,
                }

    return None
