# Entrypoint: initializes DB, optionally MT5 initialization, and launches webhook + scanner
import asyncio
from . import config
from .db import init_db
import uvicorn
from .webhook import webhook
from .scanner_worker import periodic_scanner_loop

def maybe_init_mt5():
    if config.PROVIDER == "mt5":
        try:
            from .data_providers import mt5_provider
            ok = mt5_provider.initialize()
            if not ok:
                print("[main] MT5 initialization returned False. Ensure terminal available.")
            else:
                print("[main] MT5 initialized successfully.")
        except Exception as e:
            print("[main] MT5 initialize/import failed:", e)

def start_webhook():
    uvicorn.run("src.webhook.webhook:app", host=config.WEBHOOK_HOST, port=config.WEBHOOK_PORT, log_level="info")

def main():
    print("[main] Initializing DB...")
    init_db()
    maybe_init_mt5()
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(periodic_scanner_loop())
        loop.run_in_executor(None, start_webhook)
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutdown requested")
    finally:
        loop.close()

if __name__ == "__main__":
    main()