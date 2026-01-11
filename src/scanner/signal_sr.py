import time
from .. import config
from .telegram import send_telegram, format_market_scan_message

def send_signals_with_dynamic_sr(signals: list, candles_data: dict, delay: float = 60.0):
    """
    Send market signals to Telegram with dynamic support/resistance filtering.

    signals: list of dicts with signal info (must have 'symbol', 'entry_low', 'entry_high', etc.)
    candles_data: dict with recent candles per symbol, each candle = {'high', 'low', 'close'}
    delay: seconds to wait between sending each alert
    """
    def calculate_dynamic_sr(candles, lookback=50):
        recent = candles[-lookback:] if len(candles) >= lookback else candles
        highs = [c['high'] for c in recent]
        lows = [c['low'] for c in recent]
        resistance = sorted(highs, reverse=True)[:3]  # top 3 highs
        support = sorted(lows)[:3]                     # bottom 3 lows
        return support, resistance

    def is_near_sr(price, support_levels, resistance_levels, buffer=0.002):
        for lvl in support_levels + resistance_levels:
            if abs(price - lvl) <= buffer:
                return True
        return False

    for sig in signals:
        symbol = sig['symbol']
        entry_mid = (sig['entry_low'] + sig['entry_high']) / 2

        # Get recent candles for this symbol
        candles = candles_data.get(symbol, [])
        support, resistance = calculate_dynamic_sr(candles)

        # Only send alert if entry is near a dynamic S/R level
        if is_near_sr(entry_mid, support, resistance):
            text = format_market_scan_message(sig)
            print("Sending Telegram payload:", {"chat_id": config.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"})
            send_telegram(text)
            time.sleep(delay)  # wait before sending the next alert
