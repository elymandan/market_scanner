# Compute retracement-based entry, SL, TPs and RR metrics
from typing import Dict
from .bos_detector import atr
from .. import config

def compute_levels(bos: Dict, htf_df, atr_value: float) -> Dict:
    dir = bos["direction"]
    bos_price = bos["bos_price"]
    last_close = bos["last_close"]
    impulse = abs(last_close - bos_price)
    if impulse == 0:
        impulse = float(htf_df['Close'].pct_change().abs().dropna().iloc[-1])
    # Define retracement zone using configured fibs
    r_low = config.RETRACEMENT_LOW
    r_high = config.RETRACEMENT_HIGH
    if dir == "long":
        zone_high = last_close - impulse * r_low
        zone_low = last_close - impulse * r_high
        entry = zone_high  # conservative entry
        stop = bos_price - atr_value * config.ATR_STOP_BUFFER
        risk = max(entry - stop, 1e-6)
        tp1 = entry + risk * 1.0
        tp2 = entry + risk * 2.0
        tp3 = entry + risk * 3.0
    else:
        zone_high = last_close + impulse * r_high
        zone_low = last_close + impulse * r_low
        entry = zone_high
        stop = bos_price + atr_value * config.ATR_STOP_BUFFER
        risk = max(stop - entry, 1e-6)
        tp1 = entry - risk * 1.0
        tp2 = entry - risk * 2.0
        tp3 = entry - risk * 3.0

    rr_tp2 = (tp2 - entry) / risk if dir == "long" else (entry - tp2) / risk
    return {
        "entry": float(entry),
        "zone_high": float(zone_high),
        "zone_low": float(zone_low),
        "stop": float(stop),
        "tp1": float(tp1),
        "tp2": float(tp2),
        "tp3": float(tp3),
        "rr_tp2": float(rr_tp2),
        "direction": dir
    }