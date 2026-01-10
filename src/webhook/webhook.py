# FastAPI webhook receiver for TradingView alerts (simple)
from fastapi import FastAPI, Header, HTTPException, Request
from .. import config, db, scanner_worker
import asyncio

app = FastAPI()

@app.post("/webhook")
async def tradingview_webhook(request: Request, x_secret: str = Header(None)):
    # optional secret verification
    if config.WEBHOOK_SECRET and x_secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")
    payload = await request.json()
    # Minimal expected fields: symbol, timeframe, event
    symbol = payload.get("symbol")
    timeframe = payload.get("timeframe")
    event = payload.get("event")
    # You can customize: translate tradingview message into internal action
    # We'll enqueue an immediate scan of the symbol
    if symbol:
        asyncio.create_task(scanner_worker.scan_symbol_and_notify(symbol.strip()))
        return {"status": "queued", "symbol": symbol}
    return {"status": "ignored"}