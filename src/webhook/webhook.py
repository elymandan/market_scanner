# Simple TradingView webhook receiver (keeps system headless; no admin endpoints)
from fastapi import FastAPI, Header, HTTPException, Request
from .. import config
import asyncio

app = FastAPI()

def _verify_secret(x_secret: str):
    if not config.WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Webhook secret not configured")
    if x_secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid secret")

# 1. REMOVE the import from the top of the file:
# from ..scanner_worker import scan_symbol_once  <-- DELETE THIS

@app.post("/webhook")
async def tradingview_webhook(request: Request, x_secret: str = Header(None)):
    _verify_secret(x_secret)
    
    # 2. ADD the import HERE inside the function
    from ..scanner_worker import scan_symbol_once
    
    payload = await request.json()
    symbol = payload.get("symbol")
    if not symbol:
        return {"status": "ignored", "reason": "no symbol"}
    
    asyncio.create_task(scan_symbol_once(symbol.strip()))
    return {"status": "queued", "symbol": symbol}