# HTF Break-of-Structure detection using swing logic and body-close rule
import numpy as np
from typing import List, Tuple, Optional, Dict
import pandas as pd
from datetime import datetime

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high = df['High']; low = df['Low']; close = df['Close']
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def find_swings(df: pd.DataFrame, left: int = 3, right: int = 3) -> Tuple[List[int], List[int]]:
    highs = df['High'].values; lows = df['Low'].values
    n = len(df)
    swing_highs = []; swing_lows = []
    for i in range(left, n - right):
        window_h = highs[i - left: i + right + 1]
        window_l = lows[i - left: i + right + 1]
        if highs[i] == window_h.max() and np.sum(window_h == highs[i]) == 1:
            swing_highs.append(i)
        if lows[i] == window_l.min() and np.sum(window_l == lows[i]) == 1:
            swing_lows.append(i)
    return swing_highs, swing_lows

def detect_bos(df: pd.DataFrame, left: int = 3, right: int = 3) -> Optional[Dict]:
    if len(df) < (left + right + 5):
        return None
    swing_highs, swing_lows = find_swings(df, left, right)
    if not swing_highs and not swing_lows:
        return None
    # Choose most recent swing extreme that is relevant to BOS
    last_idx = len(df) - 1
    # previous swing that could be broken is the most recent swing opposite to last observed
    # Find last swing high and low
    last_high = swing_highs[-1] if swing_highs else None
    last_low = swing_lows[-1] if swing_lows else None

    # Choose the most recent completed swing (greatest index)
    last_swing_idx = max([i for i in [last_high, last_low] if i is not None])
    # Get prior opposite swing to be broken
    prior_highs = [i for i in swing_highs if i < last_swing_idx]
    prior_lows = [i for i in swing_lows if i < last_swing_idx]

    # For simplicity: determine break against the most recent prior extreme (if exists)
    # Use last candle body close to determine whether break occurred
    last_close = float(df['Close'].iloc[-1])
    last_open = float(df['Open'].iloc[-1])

    # If there is a prior swing high and the last close > prior high => BOS long
    if prior_highs:
        prev_high_idx = prior_highs[-1]
        prev_high_price = float(df['High'].iloc[prev_high_idx])
        if last_close > prev_high_price:
            return {
                "direction": "long",
                "bos_price": prev_high_price,
                "bos_ts": df.index[-1].isoformat(),
                "last_close": last_close,
                "last_open": last_open
            }
    # If there is a prior swing low and last close < prior low => BOS short
    if prior_lows:
        prev_low_idx = prior_lows[-1]
        prev_low_price = float(df['Low'].iloc[prev_low_idx])
        if last_close < prev_low_price:
            return {
                "direction": "short",
                "bos_price": prev_low_price,
                "bos_ts": df.index[-1].isoformat(),
                "last_close": last_close,
                "last_open": last_open
            }
    return None