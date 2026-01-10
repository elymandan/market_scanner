# HTF-BOS Auto Alert System (Break-of-Structure + Pullback Entry Scanner)

Overview
- Detects HTF Break of Structure (BOS) using candle-body closes (H4 / 2H).
- Watches lower timeframe for pullbacks and proposes Entry, Stop-Loss, and TP levels.
- Works with MetaTrader5 (recommended for live FX/CFD) or Yahoo Finance for testing.
- Sends alerts to Telegram and WhatsApp (via Twilio). Also accepts TradingView webhooks.
- Persists events in SQLite to avoid duplicate alerts and to audit signals.

Architecture
- src/data_providers: ADAPTER layer (MT5 and Yahoo fallback).
- src/scanner: BOS detection, entry/SL/TP calculation.
- src/notifier: Telegram + Twilio.
- src/webhook: FastAPI server for incoming alerts from TradingView.
- src/db: SQLite persistence for dedupe/audit.
- Async main loop that schedules periodic scans and runs the webhook server.

Quick start (dev/testing)
1. Clone repo.
2. Create a Python venv and install dependencies:
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
3. Edit `src/config.py`: set TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TWILIO_* and provider mode (MT5 vs YF).
4. For quick test use Yahoo provider (no MT5 required). Then run:
   python -m src.main
5. To run webhook server + scanner together use Docker (see docker-compose.yml).

Switching to MT5 (live):
- Install MetaTrader5 on same host, ensure terminal is running and symbols available.
- Set PROVIDER = "mt5" in config and configure any symbol mapping if needed.
- The MT5 provider uses MetaTrader5 Python package.

Notes & next steps
- Backtest your rules before trading live. This repo is a scanner/alert system, not an execution engine.
- Add account position-sizing & execution (paper-trade via broker API).
- For scale, move SQLite -> Postgres and run multiple worker replicas behind a task queue.

Files included below. Read `src/config.py` first to configure.
