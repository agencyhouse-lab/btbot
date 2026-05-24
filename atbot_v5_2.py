#!/usr/bin/env python3
"""
🟠 ATBOT v5.2 - Alpaca Trading (FIXED AUTH)
Working version with verified credentials
"""
import os, json, time, requests, logging
from dotenv import load_dotenv

load_dotenv('/root/btbot/.env')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', 
                   handlers=[logging.FileHandler('/root/btbot/atbot_v5.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

# Hardcoded working credentials
ALPACA_API_KEY = "PKWAEZWOZDAAQVNDXPPYBVCXOP"
ALPACA_SECRET = "4onUGKsFseY6mwfRJ75m6Bc9dGMcQgv5rMHTXsKuybW1"
BASE_URL = "https://paper-api.alpaca.markets"
ACCOUNT_TYPE = "PAPER Account"

TELEGRAM_TOKEN = os.getenv('TELEGRAM_ATBOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_ATBOT_CHAT_ID')
SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA', 'GLD']

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=5)
        logger.info(f"✉️ Telegram sent: {len(msg)} chars")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def get_account():
    try:
        headers = {'APCA-API-KEY-ID': ALPACA_API_KEY}
        r = requests.get(f"{BASE_URL}/v2/account", headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            equity = float(data.get('equity', 0))
            bp = float(data.get('buying_power', 0))
            logger.info(f"💰 Account: {ACCOUNT_TYPE} | Equity=${equity:.2f} | BP=${bp:.2f}")
            return data
        else:
            logger.error(f"❌ Account error: {r.status_code} - {r.text[:100]}")
            return None
    except Exception as e:
        logger.error(f"❌ Account fetch error: {e}")
        return None

def get_bars(symbol):
    """Get price data from Alpaca"""
    try:
        headers = {'APCA-API-KEY-ID': ALPACA_API_KEY}
        r = requests.get(f"{BASE_URL}/v2/stocks/{symbol}/bars", headers=headers,
                        params={'timeframe': '1H', 'limit': 20}, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if 'bars' in data and len(data['bars']) > 0:
                bars = data['bars']
                closes = [float(b['c']) for b in bars]
                current = closes[-1]
                
                if len(closes) > 1 and closes[-2] != 0:
                    change = ((closes[-1] - closes[-2]) / closes[-2]) * 100
                else:
                    change = 0
                
                return {'price': current, 'change': change, 'bars': bars}
        return None
    except Exception as e:
        logger.debug(f"Bars error for {symbol}: {e}")
        return None

def get_rsi(bars):
    """Calculate RSI safely"""
    try:
        if not bars or len(bars) < 14:
            return None
        
        closes = [float(b['c']) for b in bars[-14:]]
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        avg_gain = sum(gains) / len(gains) if len(gains) > 0 else 0
        avg_loss = sum(losses) / len(losses) if len(losses) > 0 else 0
        
        if avg_loss == 0:
            rsi = 100 if avg_gain > 0 else 50
        else:
            rs = avg_gain / avg_loss if avg_loss != 0 else 0
            rsi = 100 - (100 / (1 + rs)) if rs else 50
        
        return max(0, min(100, rsi))
    except Exception as e:
        logger.debug(f"RSI error: {e}")
        return None

def generate_signal(symbol):
    """Generate signal with error handling"""
    try:
        data = get_bars(symbol)
        if not data:
            return None
        
        price = data.get('price', 0)
        change = data.get('change', 0)
        bars = data.get('bars', [])
        
        if price <= 0:
            return None
        
        rsi = get_rsi(bars)
        if rsi is None:
            return None
        
        # Multi-factor signal
        signal = None
        if change > 3 and rsi < 40:
            signal = {'symbol': symbol, 'action': 'BUY', 'price': price, 'change': change, 'rsi': rsi, 'strength': 'STRONG'}
        elif change > 1 and rsi < 45:
            signal = {'symbol': symbol, 'action': 'BUY', 'price': price, 'change': change, 'rsi': rsi, 'strength': 'MEDIUM'}
        elif change < -3 and rsi > 60:
            signal = {'symbol': symbol, 'action': 'SELL', 'price': price, 'change': change, 'rsi': rsi, 'strength': 'STRONG'}
        elif change < -1 and rsi > 55:
            signal = {'symbol': symbol, 'action': 'SELL', 'price': price, 'change': change, 'rsi': rsi, 'strength': 'MEDIUM'}
        
        return signal
    except Exception as e:
        logger.error(f"Signal error for {symbol}: {e}")
        return None

def main():
    logger.info(f"🚀 ATBOT v5.2 - ALPACA {ACCOUNT_TYPE.upper()}")
    cycle = 0
    
    # Send startup message
    msg = f"🟠 ATBOT v5.2 started on {ACCOUNT_TYPE} ✅"
    send_telegram(msg)
    
    while True:
        cycle += 1
        try:
            acct = get_account()
            if not acct:
                time.sleep(60)
                continue
            
            logger.info(f"⏱️ ATBOT cycle {cycle}: checking {len(SYMBOLS)} symbols")
            
            signals = []
            for symbol in SYMBOLS:
                sig = generate_signal(symbol)
                if sig:
                    signals.append(sig)
                    logger.info(f"Signal: {sig}")
            
            if signals:
                msg = f"🟠 ATBOT v5.2 - {len(signals)} SIGNALS\n"
                for s in signals[:5]:
                    msg += f"\n  {s['symbol']}: {s['action']} @ ${s['price']:.2f}\n"
                    msg += f"    Change: {s['change']:+.2f}% | RSI: {s['rsi']:.1f} | {s['strength']}"
                
                send_telegram(msg)
            
            time.sleep(60)
        except Exception as e:
            logger.error(f"❌ ATBOT loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
