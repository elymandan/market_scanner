# Core orchestration: uses provider to fetch HTF/LTF, detect BOS, compute levels and notify
import asyncio
from . import config
from .db import insert_signal, init_db, mark_bos_sent, mark_market_sent, get_signal, update_pulled_back, mark_notified_channel
from .scanner.bos_detector import detect_bos, atr as calc_atr
from .scanner.entry_finder import compute_levels
from .notifier import telegram, twilio_whatsapp

# lazy import of providers
from .data_providers import yf_provider, mt5_provider

async def scan_symbol_and_notify(symbol: str):
    # Fetch HTF and LTF depending on provider
    provider = config.PROVIDER
    if provider == "mt5":
        htf_df = mt5_provider.fetch_ohlcv(symbol, config.HTF)
        ltf_df = mt5_provider.fetch_ohlcv(symbol, config.LTF, count=500)
    else:
        htf_df = yf_provider.fetch_ohlcv(symbol, config.HTF)
        ltf_df = yf_provider.fetch_ohlcv(symbol, config.LTF)

    if htf_df is None or ltf_df is None:
        return

    bos = detect_bos(htf_df, left=config.SWING_LEFT, right=config.SWING_RIGHT)
    if not bos:
        return

    # compute ATR on HTF for SL sizing
    atr_series = calc_atr(htf_df, n=config.ATR_PERIOD)
    atr_value = float(atr_series.iloc[-1])

    levels = compute_levels(bos, htf_df, atr_value)

    # inspect LTF for pullback (allow wick)
    ltf_low = float(ltf_df['Low'].iloc[-1])
    ltf_high = float(ltf_df['High'].iloc[-1])
    pulled = False
    if levels['direction'] == "long":
        if ltf_low <= levels['zone_high'] and ltf_high >= levels['zone_low']:
            pulled = True
    else:
        if ltf_high >= levels['zone_low'] and ltf_low <= levels['zone_high']:
            pulled = True

    sig = {
        "symbol": symbol,
        "bos_ts": bos["bos_ts"],
        "direction": levels["direction"],
        "entry": levels["entry"],
        "entry_low": levels["zone_low"],
        "entry_high": levels["zone_high"],
        "stop": levels["stop"],
        "tp1": levels["tp1"],
        "tp2": levels["tp2"],
        "tp3": levels["tp3"],
        "atr": atr_value,
        "pulled_back": int(pulled),
        "rr_tp2": levels.get("rr_tp2", 0.0)
    }

    # Try inserting; if it exists, fetch DB record to see notified flags
    inserted = insert_signal(sig)
    db_record = get_signal(symbol, sig["bos_ts"])
    if not db_record:
        # this should not happen normally, but bail if we can't read the existing record
        return

    # 1) BOS alert: send immediately if not sent
    if not db_record.get("notified_bos", 0):
        # prepare BOS message payload as required format
        bos_msg_payload = {
            "symbol": symbol,
            "direction": sig["direction"],
            "bos_tf": config.HTF,
            "entry_low": sig["entry_low"],
            "entry_high": sig["entry_high"],
            "stop": sig["stop"],
            "tp1": sig["tp1"],
            "tp2": sig["tp2"],
            "status": "Waiting for pullback"
        }
        text = telegram.format_bos_message(bos_msg_payload)
        sent = telegram.send_telegram(text)
        if sent:
            mark_bos_sent(symbol, sig["bos_ts"])
            mark_notified_channel(symbol, sig["bos_ts"], "telegram")
        # Whatsapp optionally
        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_WHATSAPP_TO:
            w_sent = twilio_whatsapp.send_whatsapp(text)
            if w_sent:
                mark_notified_channel(symbol, sig["bos_ts"], "whatsapp")

    # 2) Market Scan Alert: send when pullback is observed (or optionally when RR threshold is met)
    # Re-read DB record to pick up updated flags
    db_record = get_signal(symbol, sig["bos_ts"])
    already_market = bool(db_record.get("notified_market", 0))

    # Update DB pulled_back field
    if pulled:
        update_pulled_back(symbol, sig["bos_ts"], 1)

    send_market_alert = False
    # send market alert when pulled back into entry zone
    if pulled and not already_market:
        send_market_alert = True
    # Optionally we could also send Market Scan earlier if RR very high even without pullback:
    elif sig.get("rr_tp2", 0.0) >= 2.0 and not already_market:
        # This line is optional: uncomment or remove depending on desired behavior.
        # send_market_alert = True
        send_market_alert = False

    if send_market_alert:
        market_payload = {
            "symbol": symbol,
            "direction": sig["direction"],
            "timeframe": config.LTF,
            "entry_low": sig["entry_low"],
            "entry_high": sig["entry_high"],
            "stop": sig["stop"],
            "tp1": sig["tp1"],
            "tp2": sig["tp2"],
            "rr_est": f"1:{sig.get('rr_tp2',0.0):.1f}",
            "reason_lines": [
                f"{'Bullish' if sig['direction']=='long' else 'Bearish'} BOS confirmed",
                "Pullback into LTF entry zone (FVG / structure)",
                f"HTF {'bullish' if config.HTF in ['4h','2h'] and sig['direction']=='long' else 'bearish' if sig['direction']=='short' else 'neutral'} bias"
            ],
            "status": "Waiting for entry"
        }
        text2 = telegram.format_market_scan_message(market_payload)
        t2 = telegram.send_telegram(text2)
        if t2:
            mark_market_sent(symbol, sig["bos_ts"])
            mark_notified_channel(symbol, sig["bos_ts"], "telegram")
        # Whatsapp optionally
        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN and config.TWILIO_WHATSAPP_TO:
            w2 = twilio_whatsapp.send_whatsapp(text2)
            if w2:
                mark_notified_channel(symbol, sig["bos_ts"], "whatsapp")