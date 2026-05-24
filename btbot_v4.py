#!/usr/bin/env python3
"""
🟠 BTBOT v4.0 - Simplified Binance Futures/Spot Bot
Direct REST API approach
"""
import os, json, time, requests, hmac, hashlib, logging
from dotenv import load_dotenv

load_dotenv('/root/btbot/.env')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('/root/btbot/btbot_v4.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
BASE_URL = "https://api.binance.com"
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BTBOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_BTBOT_CHAT_ID')
PAIRS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOGEUSDT']

def sign_request(params):
    query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
    signature = hmac.new(SECRET_KEY.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature
    return params

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=5)
        logger.info(f"✉️ Telegram sent: {len(msg)} chars")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def get_account():
    try:
        timestamp = int(time.time() * 1000)
        params = {'timestamp': timestamp}
        params = sign_request(params)
        headers = {'X-MBX-APIKEY': API_KEY}
        url = f"{BASE_URL}/api/v3/account"
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            balances = [b for b in data['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
            logger.info(f"✅ BTBOT: Connected - {len(balances)} non-zero balances")
            return data
        else:
            logger.error(f"❌ BTBOT Account error: {r.status_code}")
            return None
    except Exception as e:
        logger.error(f"❌ Account fetch error: {e}")
        return None

def get_price(symbol):
    try:
        url = f"{BASE_URL}/api/v3/ticker/price"
        r = requests.get(url, params={'symbol': symbol}, timeout=10)
        if r.status_code == 200:
            return float(r.json()['price'])
        return None
    except:
        return None

def get_rsi(symbol):
    """Get RSI from 15-min candles"""
    try:
        url = f"{BASE_URL}/api/v3/klines"
        params = {'symbol': symbol, 'interval': '15m', 'limit': 14}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            candles = r.json()
            closes = [float(c[4]) for c in candles]
            deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
            gains = [d if d > 0 else 0 for d in deltas]
            losses = [-d if d < 0 else 0 for d in deltas]
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi = 100 - (100 / (1 + rs))
            return rsi
        return None
    except:
        return None

def generate_signal(symbol):
    try:
        price = get_price(symbol)
        if not price:
            return None
        rsi = get_rsi(symbol)
        if rsi is None:
            return None
        if rsi < 30:
            return {'symbol': symbol, 'action': 'BUY', 'price': price, 'rsi': rsi}
        elif rsi > 70:
            return {'symbol': symbol, 'action': 'SELL', 'price': price, 'rsi': rsi}
        return None
    except Exception as e:
        logger.error(f"Signal error for {symbol}: {e}")
        return None

def main():
    logger.info("🚀 BTBOT v4.0 - SIMPLIFIED REST API")
    cycle = 0
    while True:
        cycle += 1
        try:
            acct = get_account()
            if not acct:
                time.sleep(60)
                continue
            logger.info(f"⏱️ BTBOT cycle {cycle}: checking {len(PAIRS)} pairs")
            signals = [generate_signal(p) for p in PAIRS]
            signals = [s for s in signals if s]
            if signals:
                msg = f"🟠 BTBOT v4 - {len(signals)} signals detected\n"
                for s in signals[:5]:
                    msg += f"  {s['symbol']}: {s['action']} @ ${s['price']:.2f} (RSI: {s['rsi']:.1f})\n"
                send_telegram(msg)
            time.sleep(60)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
