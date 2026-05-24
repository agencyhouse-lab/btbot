#!/usr/bin/env python3
# main.py — ps1trade PAPER trading entry point
# NO real orders placed — simulates trades with virtual balance
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bot_engine import BotEngine
from logger import log

if __name__ == "__main__":
    log.info("=" * 50)
    log.info("  ps1trade v2.1 — PAPER Trading Bot")
    log.info("  ⚠️  NO REAL ORDERS — Simulation only")
    log.info("=" * 50)
    BotEngine().start()
