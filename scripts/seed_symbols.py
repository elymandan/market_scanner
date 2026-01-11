#!/usr/bin/env python3
"""
Seed the scanner SQLite DB symbols table from a symbols file.

Usage (host):
  python scripts/seed_symbols.py symbols.txt

Usage (docker):
  docker compose run --rm scanner python /app/scripts/seed_symbols.py /app/symbols.txt
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src import db

def main():
    if len(sys.argv) < 2:
        print("Usage: seed_symbols.py <symbols_file>")
        return
    path = sys.argv[1]
    if not os.path.exists(path):
        print("File not found:", path); return
    db.init_db()
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"): continue
            ok = db.add_symbol(s, source="file")
            if ok:
                count += 1
    print(f"Seeded {count} symbols from {path}")

if __name__ == "__main__":
    main()