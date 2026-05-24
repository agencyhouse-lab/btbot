#!/usr/bin/env python3
"""
🟠 ATBOT v4.0 - Simplified Alpaca Trading Bot
Direct REST API - No complex dependencies
"""
import os, json, time, requests, logging
from dotenv import load_dotenv

load_dotenv('/root/btbot/.env')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('/root/btbot/atbot_v4.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = "https://api.alpaca.markets"
headers_v2 = {'APCA-API-KEY-ID': ALPACA_API_KEY, 'Content-Type': 'application/json'}
DATA_URL = "https://data.alpaca.markets"
TELEGRAM_TOKEN = os.getenv('TELEGRAM_ATBOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_ATBOT_CHAT_ID')
SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA', 'GLD', 'SLV', 'USO', 'DBC', 'DBA']
headers = {'APCA-API-KEY-ID': ALPACA_API_KEY}

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=5)
        logger.info(f"✉️ Telegram sent: {len(msg)} chars")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def get_account():
    try:
        r = requests.get(f"{BASE_URL}/v2/account", headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            equity = float(data.get('equity', 0))
            bp = float(data.get('buying_power', 0))
            logger.info(f"💰 ATBOT Account: Equity=${equity:.2f} | BP=${bp:.2f}")
            return data
        logger.error(f"Account error: {r.status_code}")
        return None
    except Exception as e:
        logger.error(f"Account fetch error: {e}")
        return None

def get_latest_bars(symbol):
    try:
        url = f"{DATA_URL}/v1beta3/stocks/{symbol}/latest/bar"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if 'bar' in data:
                bar = data['bar']
                return {'c': float(bar.get('c', 0)), 'h': float(bar.get('h', 0)), 'l': float(bar.get('l', 0)), 'v': float(bar.get('v', 0))}
        logger.warning(f"⚠️ No data for {symbol}: {r.status_code}")
        return None
    except Exception as e:
        logger.warning(f"⚠️ Signal error for {symbol}: {e}")
        return None

def generate_signal(symbol):
    try:
        bar = get_latest_bars(symbol)
        if not bar:
            return None
        close, high, low = bar['c'], bar['h'], bar['l']
        range_pct = (high - low) / low if low > 0 else 0
        if close >= high * 0.98 and range_pct > 0.005:
            return {'symbol': symbol, 'action': 'BUY', 'price': close, 'signal': 80}
        elif close <= low * 1.02 and range_pct > 0.005:
            return {'symbol': symbol, 'action': 'SELL', 'price': close, 'signal': 80}
        return None
    except Exception as e:
        logger.error(f"Signal error for {symbol}: {e}")
        return None

def main():
    logger.info("🚀 ATBOT v4.0 - SIMPLIFIED REST API")
    cycle = 0
    while True:
        cycle += 1
        try:
            acct = get_account()
            if not acct:
                time.sleep(60)
                continue
            logger.info(f"⏱️ ATBOT cycle {cycle}: checking {len(SYMBOLS)} symbols")
            signals = [generate_signal(s) for s in SYMBOLS]
            signals = [s for s in signals if s]
            if signals:
                msg = f"🟠 ATBOT v4 - {len(signals)} signals\n"
                for s in signals[:5]:
                    msg += f"  {s['symbol']}: {s['action']} @ ${s['price']:.2f}\n"
                send_telegram(msg)
            time.sleep(60)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
