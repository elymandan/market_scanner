# Central configuration (environment-driven)
import os

# ----------------------------
# Provider & Timeframes
# ----------------------------

# Provider: "mt5" (recommended for broker symbols) or "yf" (Yahoo Finance)
PROVIDER = os.getenv("PROVIDER", "yf").lower()

# Timeframes
HTF = os.getenv("HTF", "4h")
LTF = os.getenv("LTF", "15m")

# ----------------------------
# Swing detection / ATR
# ----------------------------

SWING_LEFT = int(os.getenv("SWING_LEFT", "3"))
SWING_RIGHT = int(os.getenv("SWING_RIGHT", "3"))

RETRACEMENT_LOW = float(os.getenv("RETRACEMENT_LOW", "0.382"))
RETRACEMENT_HIGH = float(os.getenv("RETRACEMENT_HIGH", "0.786"))

ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
ATR_STOP_BUFFER = float(os.getenv("ATR_STOP_BUFFER", "0.5"))

# ----------------------------
# Risk:Reward thresholds
# ----------------------------

RR_MIN_ALERT = float(os.getenv("RR_MIN_ALERT", os.getenv("RR_MIN", "5.0")))
RR_MIN_STORE = float(os.getenv("RR_MIN_STORE", "3.0"))

# ----------------------------
# Scanner / concurrency
# ----------------------------

SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))
SCAN_CONCURRENCY = int(os.getenv("SCAN_CONCURRENCY", "8"))

# Heartbeat interval (seconds). 0 disables
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "3600"))

# ----------------------------
# Symbols
# ----------------------------

SYMBOLS_FILE = os.getenv("SYMBOLS_FILE", "symbols.txt").strip()
SYMBOLS_MAX = int(os.getenv("SYMBOLS_MAX", "0"))

SYMBOLS = []
if os.path.exists(SYMBOLS_FILE):
    with open(SYMBOLS_FILE, "r", encoding="utf-8-sig") as f:
        SYMBOLS = [line.strip().upper() for line in f if line.strip() and not line.startswith("#")]
    if SYMBOLS_MAX > 0:
        SYMBOLS = SYMBOLS[:SYMBOLS_MAX]
else:
    print(f"WARNING: Symbol file {SYMBOLS_FILE} not found.")

# ----------------------------
# Notification credentials
# ----------------------------

# IMPORTANT: No fallback token here — must be set in environment
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Must be set in .env or Docker environment
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")      # Must be set in .env or Docker environment

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO", "")

# ----------------------------
# Persistence & server
# ----------------------------

DB_PATH = os.getenv("DB_PATH", "signals.db")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "changeme")

# ----------------------------
# Startup checks (optional but recommended)
# ----------------------------

if TELEGRAM_BOT_TOKEN is None or TELEGRAM_CHAT_ID is None:
    print("WARNING: Telegram bot token or chat ID not set! Telegram alerts will be skipped.")
