#!/usr/bin/env python3
# main.py — btbot LIVE trading entry point
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bot_engine import BotEngine
from logger import log

if __name__ == "__main__":
    log.info("=" * 50)
    log.info("  btbot v2.1 — LIVE Binance Trading Bot")
    log.info("=" * 50)
    BotEngine().start()
