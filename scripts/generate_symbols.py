#!/usr/bin/env python3
"""
Generate provider-specific symbols.txt from a human-readable preferred list.

Usage:
  python scripts/generate_symbols.py --provider yf --preferred preferred_list.txt --out symbols.txt
  python scripts/generate_symbols.py --provider mt5 --preferred preferred_list.txt --out symbols.txt
"""
import argparse
import os

# Mapping for yfinance (primary choices). Adjust if you prefer ETFs vs futures for some items.
MAPPING_YF = {
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "USDJPY=X",
    "GER40": "^GDAXI",
    "USOIL": "CL=F",
    "UKOIL": "BZ=F",
    "NAS100": "QQQ",
    "US30": "^DJI",
    "EURJPY": "EURJPY=X",
    "GBPJPY": "GBPJPY=X",
    "USDCAD": "USDCAD=X",
    "NZDJPY": "NZDJPY=X",
    "NZDUSD": "NZDUSD=X",
    "GBPAUD": "GBPAUD=X",
    "EURAUD": "EURAUD=X",
    "US500": "^GSPC",
    "US 500": "^GSPC",
    # stocks pass through
    "AAPL": "AAPL",
    "MSFT": "MSFT",
    "AMZN": "AMZN",
    "NVDA": "NVDA",
    "TSLA": "TSLA",
    "GOOGL": "GOOGL",
    # synonyms
    "US 500": "^GSPC",
    "US500": "^GSPC",
}

def normalize_name(name: str) -> str:
    return name.strip().upper().replace(" ", "")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--provider", choices=("yf","mt5"), required=True)
    p.add_argument("--preferred", default="preferred_list.txt")
    p.add_argument("--out", default="symbols.txt")
    args = p.parse_args()

    if not os.path.exists(args.preferred):
        print("Preferred list not found:", args.preferred)
        return

    out_lines = []
    with open(args.preferred, "r", encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            key = s.strip()
            if args.provider == "mt5":
                # For MT5, use original symbol but sanitized (no spaces)
                candidate = key.replace(" ", "").upper()
                out_lines.append(candidate)
            else:
                # yfinance mapping (fallback: try name with =X variant)
                key_up = key.strip().upper()
                mapped = MAPPING_YF.get(key_up)
                if not mapped:
                    # try generic mapping with =X (common for forex)
                    if len(key_up) == 6:  # e.g. EURUSD
                        mapped = key_up[:3] + key_up[3:] + "=X"
                    else:
                        mapped = key_up
                out_lines.append(mapped)

    with open(args.out, "w", encoding="utf-8") as fo:
        for x in out_lines:
            fo.write(x + "\n")
    print("Wrote", len(out_lines), "symbols to", args.out)

if __name__ == "__main__":
    main()