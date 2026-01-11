# Telegram notification helper with the exact two-format outputs you requested
import requests
from .. import config
from datetime import datetime

def send_telegram(text: str) -> bool:
    token = config.TELEGRAM_BOT_TOKEN
    chat = config.TELEGRAM_CHAT_ID

    # Only skip if missing or empty
    if not token or token.strip() == "":
        print("Telegram send skipped: TELEGRAM_BOT_TOKEN not set.")
        return False
    if not chat or str(chat).strip() == "":
        print("Telegram send skipped: TELEGRAM_CHAT_ID not set.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat, "text": text, "parse_mode": "HTML"}

    # Debug: log the payload before sending
    print("Sending Telegram payload:", payload)

    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except requests.exceptions.HTTPError as http_err:
        print(f"Telegram send failed: {http_err} - Response: {r.text}")
        return False
    except Exception as e:
        print("Telegram send failed with unexpected error:", e)
        return False


def format_market_scan_message(sig: dict) -> str:
    s = []
    s.append("📊 MARKET SCAN ALERT\n")
    s.append(f"Instrument: {sig['symbol']}")
    s.append(f"Direction: {sig['direction'].upper()}")
    s.append(f"Timeframe: {sig.get('timeframe', config.LTF)}\n")
    s.append(f"📌 Entry Zone: {sig['entry_low']:.5f} – {sig['entry_high']:.5f}")
    s.append(f"🛑 Stop Loss: {sig['stop']:.5f}")
    s.append(f"🎯 TP1: {sig['tp1']:.5f}")
    s.append(f"🎯 TP2: {sig['tp2']:.5f}")
    s.append(f"R:R ≈ 1:{sig.get('rr_est_num', 0):.1f}\n")
    s.append("Reason:")
    for r in sig.get('reason_lines', []):
        s.append(f"• {r}")
    s.append(f"\nStatus: {sig.get('status','Waiting for entry')}")
    return "\n".join(s)


def format_bos_message(sig: dict) -> str:
    s = []
    s.append("🟡 BOS CONFIRMED – TRADE IDEA\n")
    s.append(f"Market: {sig['symbol']}")
    s.append(f"Direction: {sig['direction'].upper()}")
    s.append(f"BOS TF: {sig.get('bos_tf', config.HTF)} (body close)\n")
    s.append("Potential Entry Area:")
    s.append(f"• {sig['entry_low']:.5f} – {sig['entry_high']:.5f} (FVG / Structure)\n")
    s.append("Projected SL:")
    s.append(f"• Above {sig['stop']:.5f}\n")
    s.append("Projected TP:")
    s.append(f"• {sig['tp1']:.5f}")
    s.append(f"• {sig['tp2']:.5f}\n")
    s.append(f"Status: {sig.get('status','Waiting for pullback')}")
    return "\n".join(s)


def format_status_message(stats: dict, symbols_count: int) -> str:
    """
    Create a short periodic status message summarizing scanner activity.
    stats: dict returned by db.get_stats()
    """
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = []
    lines.append("🔎 Scanner status update")
    lines.append(f"Time: {now}")
    lines.append(f"Universe size: {symbols_count} instruments")
    lines.append(f"Signals stored: {stats.get('total_signals', 0)}")
    lines.append(f"Market alerts sent: {stats.get('market_sent', 0)}")
    lines.append(f"Candidate signals (with TP/SL set): {stats.get('candidates', 0)}")
    lines.append("")
    lines.append("Note: live alerts are sent for setups with R:R >= 1:{}".format(int(config.RR_MIN_ALERT)))
    lines.append("Lower-RR setups are stored for review (RR >= {}).".format(int(config.RR_MIN_STORE)))
    return "\n".join(lines)

def send_signals_staggered(signals: list, delay: float = 60.0):
    """
    Send all signals to Telegram with a small delay between each to prevent flooding.
    delay: seconds to wait between each alert
    """
    for sig in signals:
        message = format_market_scan_message(sig) if sig.get("type") == "pullback" else format_bos_message(sig)
        if send_telegram(message):
            print(f"[Worker] Sent alert for {sig['symbol']}")
        time.sleep(delay)