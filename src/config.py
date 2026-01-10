# Central configuration (edit values or use environment variables)
import os

# Provider: "mt5" (recommended for Forex/CFD live) or "yf" (yfinance for testing)
PROVIDER = os.getenv("PROVIDER", "yf")

# Timeframes
HTF = os.getenv("HTF", "4h")   # allowed: "4h", "2h"
LTF = os.getenv("LTF", "15m")  # allowed: "15m", "5m"

# Scanner parameters
SWING_LEFT = int(os.getenv("SWING_LEFT", "3"))
SWING_RIGHT = int(os.getenv("SWING_RIGHT", "3"))
RETRACEMENT_LOW = float(os.getenv("RETRACEMENT_LOW", "0.382"))
RETRACEMENT_HIGH = float(os.getenv("RETRACEMENT_HIGH", "0.786"))
ATR_PERIOD = int(os.getenv("ATR_PERIOD", "14"))
ATR_STOP_BUFFER = float(os.getenv("ATR_STOP_BUFFER", "0.5"))
ELITE_RR_THRESHOLD = float(os.getenv("ELITE_RR_THRESHOLD", "3.0"))  # 1:3 filter

# Notifier / webhook
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "REPLACE_ME")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "REPLACE_ME")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+1415...")  # Twilio sandbox number
TWILIO_WHATSAPP_TO = os.getenv("TWILIO_WHATSAPP_TO", "")  # your number e.g. whatsapp:+1234567890

# Database
DB_PATH = os.getenv("DB_PATH", "signals.db")

# Symbols to scan (edit for your universe)
SYMBOLS = os.getenv("SYMBOLS", "EURUSD=X,GBPUSD=X,AAPL,SPY").split(",")

# Scan scheduling
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "300"))  # 5 minutes

# Server
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "0.0.0.0")
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8000"))

# TradingView webhook secret (optional)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "changeme")