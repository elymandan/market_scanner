# Entrypoint: initializes DB, optionally MT5, and launches webhook + scanner
import asyncio
import uvicorn
from . import config
from .db import init_db
from .webhook.webhook import app
import os

from . import scanner_worker
from .data_providers import mt5_provider

def start_webhook():
    # Run uvicorn in background thread via asyncio create_task
    config_uvicorn = {
        "app": "src.webhook.webhook:app",
        "host": config.WEBHOOK_HOST,
        "port": config.WEBHOOK_PORT,
        "log_level": "info",
        "reload": False
    }
    # Use uvicorn.run in a thread to keep it simple for this example
    uvicorn.run("src.webhook.webhook:app", host=config.WEBHOOK_HOST, port=config.WEBHOOK_PORT)

def main():
    print("Initializing DB...")
    init_db()
    if config.PROVIDER == "mt5":
        print("Initializing MT5...")
        ok = mt5_provider.initialize()
        if not ok:
            print("MT5 initialization failed. Check terminal & path.")
    # Run webhook server and scanner loop concurrently
    loop = asyncio.get_event_loop()
    try:
        # start scanner as background task
        loop.create_task(scanner_worker.periodic_scanner_loop())
        # start webhook server (blocking) - run in thread via run_in_executor
        loop.run_in_executor(None, start_webhook)
        loop.run_forever()
    except KeyboardInterrupt:
        print("Shutdown requested")
    finally:
        loop.close()

if __name__ == "__main__":
    main()