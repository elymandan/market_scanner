# Telegram notification helper with two alert formats
import requests
from .. import config

def send_telegram(text: str) -> bool:
    token = config.TELEGRAM_BOT_TOKEN
    chat = config.TELEGRAM_CHAT_ID
    if not token or not chat:
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print("Telegram error:", e)
        return False

def format_market_scan_message(sig: dict) -> str:
    """
    Format the MARKET SCAN ALERT (detailed entry zone) — sent when pullback into entry zone occurs.
    Expected sig keys: symbol, direction, timeframe, entry_low, entry_high, stop, tp1, tp2, rr_est, reason_lines (list), status
    """
    lines = []
    lines.append("📊 MARKET SCAN ALERT\n")
    lines.append(f"Instrument: {sig['symbol']}")
    lines.append(f"Direction: {sig['direction'].upper()}")
    lines.append(f"Timeframe: {sig.get('timeframe', config.LTF)}\n")
    lines.append(f"📌 Entry Zone: {sig['entry_low']:.5f} – {sig['entry_high']:.5f}")
    lines.append(f"🛑 Stop Loss: {sig['stop']:.5f}")
    lines.append(f"🎯 TP1: {sig['tp1']:.5f}")
    lines.append(f"🎯 TP2: {sig['tp2']:.5f}")
    lines.append(f"R:R ≈ {sig.get('rr_est','')}\n")
    lines.append("Reason:")
    for r in sig.get('reason_lines', []):
        lines.append(f"• {r}")
    lines.append(f"\nStatus: {sig.get('status','Waiting for entry')}")
    # join with newlines
    return "\n".join(lines)

def format_bos_message(sig: dict) -> str:
    """
    Format the BOS CONFIRMED — TRADE IDEA message (sent immediately when BOS detected).
    Expected sig keys: symbol, direction, bos_tf, entry_low, entry_high, stop, tp1, tp2, status
    """
    lines = []
    lines.append("🟡 BOS CONFIRMED – TRADE IDEA\n")
    lines.append(f"Market: {sig['symbol']}")
    lines.append(f"Direction: {sig['direction'].upper()}")
    lines.append(f"BOS TF: {sig.get('bos_tf', config.HTF)} (body close)\n")
    lines.append("Potential Entry Area:")
    lines.append(f"• {sig['entry_low']:.5f} – {sig['entry_high']:.5f} (FVG / Structure)\n")
    lines.append("Projected SL:")
    lines.append(f"• Above {sig['stop']:.5f}\n")
    lines.append("Projected TP:")
    lines.append(f"• {sig['tp1']:.5f}")
    lines.append(f"• {sig['tp2']:.5f}\n")
    lines.append(f"Status: {sig.get('status','Waiting for pullback')}")
    return "\n".join(lines)