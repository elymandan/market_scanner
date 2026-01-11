import asyncio
from datetime import datetime

from . import config
from .db import (
    insert_signal,
    mark_bos_sent,
    mark_market_sent,
    get_signal,
    update_pulled_back,
    mark_notified_channel,
)
from .scanner.bos_detector import detect_bos, atr as calc_atr
from .scanner.entry_finder import compute_levels
from .notifier import telegram


async def scan_symbol_and_notify(symbol: str):
    provider = config.PROVIDER
    htf_df, ltf_df = None, None

    # -------------------------------------------------
    # 1. Fetch Data
    # -------------------------------------------------
    try:
        if provider == "mt5":
            from .data_providers import mt5_provider
            htf_df = mt5_provider.fetch_ohlcv(symbol, config.HTF)
            ltf_df = mt5_provider.fetch_ohlcv(symbol, config.LTF, count=500)
        else:
            from .data_providers import yf_provider
            htf_df = yf_provider.fetch_ohlcv(symbol, config.HTF)
            ltf_df = yf_provider.fetch_ohlcv(symbol, config.LTF)
    except Exception as e:
        print(f"[Worker] Error fetching {symbol}: {e}")
        return

    if (
        htf_df is None
        or ltf_df is None
        or htf_df.empty
        or ltf_df.empty
    ):
        return

    # -------------------------------------------------
    # 2. Strategy Logic: Detect BOS
    # -------------------------------------------------
    bos = detect_bos(
        htf_df,
        left=config.SWING_LEFT,
        right=config.SWING_RIGHT,
    )
    if not bos:
        return

    # -------------------------------------------------
    # 3. Calculate Fibonacci / FVG Levels
    # -------------------------------------------------
    atr_series = calc_atr(htf_df, n=config.ATR_PERIOD)
    try:
        atr_value = atr_series.iloc[-1].item()
    except (IndexError, ValueError):
        return

    levels = compute_levels(bos, htf_df, atr_value)

    # -------------------------------------------------
    # 4. Check for Pullback (Current LTF Candle)
    # -------------------------------------------------
    try:
        ltf_low = ltf_df["Low"].iloc[-1].item()
        ltf_high = ltf_df["High"].iloc[-1].item()
    except (IndexError, ValueError):
        return

    pulled = False
    if levels["direction"] == "long":
        if ltf_low <= levels["zone_high"] and ltf_high >= levels["zone_low"]:
            pulled = True
    else:
        if ltf_high >= levels["zone_low"] and ltf_low <= levels["zone_high"]:
            pulled = True

    # -------------------------------------------------
    # 5. Signal Object
    # -------------------------------------------------
    sig = {
        "symbol": symbol,
        "bos_ts": bos["bos_ts"],
        "direction": levels["direction"],
        "entry_low": levels["zone_low"],
        "entry_high": levels["zone_high"],
        "stop": levels["stop"],
        "tp1": levels["tp1"],
        "tp2": levels["tp2"],
        "tp3": levels["tp3"],
        "atr": atr_value,
        "pulled_back": int(pulled),
        "rr_tp2": levels.get("rr_tp2", 0.0),
    }

    # -------------------------------------------------
    # 6. Database Synchronization
    # -------------------------------------------------
    insert_signal(sig)
    db_record = get_signal(symbol, sig["bos_ts"])
    if not db_record:
        return

    # -------------------------------------------------
    # ALERT 1: BOS DETECTED (Only Once)
    # -------------------------------------------------
    if not db_record.get("notified_bos", 0):
        bos_payload = {
            "symbol": symbol,
            "direction": sig["direction"],
            "bos_tf": config.HTF,
            "entry_low": sig["entry_low"],
            "entry_high": sig["entry_high"],
            "stop": sig["stop"],
            "tp1": sig["tp1"],
            "tp2": sig["tp2"],
            "status": "HTF BOS - Waiting for Pullback",
        }

        text = telegram.format_bos_message(bos_payload)
        if telegram.send_telegram(text):
            mark_bos_sent(symbol, sig["bos_ts"])
            print(f"[Worker] Sent BOS alert for {symbol}")

    # -------------------------------------------------
    # ALERT 2: PULLBACK OBSERVED (Only Once)
    # -------------------------------------------------
    already_market = bool(db_record.get("notified_market", 0))

    if pulled:
        update_pulled_back(symbol, sig["bos_ts"], 1)

    if pulled and not already_market:
        market_payload = {
            "symbol": symbol,
            "direction": sig["direction"],
            "timeframe": config.LTF,
            "entry_low": sig["entry_low"],
            "entry_high": sig["entry_high"],
            "stop": sig["stop"],
            "tp1": sig["tp1"],
            "tp2": sig["tp2"],
            "rr_est": f"1:{sig.get('rr_tp2', 0.0):.1f}",
            "reason_lines": [
                f"{sig['direction'].upper()} BOS confirmed",
                "Price entered Golden Zone / FVG",
            ],
            "status": "ENTRY TRIGGERED",
        }

        text2 = telegram.format_market_scan_message(market_payload)
        if telegram.send_telegram(text2):
            mark_market_sent(symbol, sig["bos_ts"])
            print(f"[Worker] Sent PULLBACK alert for {symbol}")


# -------------------------------------------------
# Concurrency & Loop
# -------------------------------------------------
sem = asyncio.Semaphore(config.SCAN_CONCURRENCY)


async def scan_with_limit(symbol: str):
    async with sem:
        return await scan_symbol_and_notify(symbol)


async def periodic_scanner_loop():
    while True:
        print(f"--- [Worker] Scan Start: {datetime.now().strftime('%H:%M:%S')} ---")

        if config.SYMBOLS:
            tasks = [scan_with_limit(s.strip()) for s in config.SYMBOLS]
            await asyncio.gather(*tasks)

        print(
            f"--- [Worker] Scan Complete. Sleeping {config.SCAN_INTERVAL_SECONDS}s ---"
        )
        await asyncio.sleep(config.SCAN_INTERVAL_SECONDS)
