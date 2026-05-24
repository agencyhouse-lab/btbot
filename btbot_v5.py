#!/usr/bin/env python3
"""
🟠 BTBOT v5.0 - Binance with Risk Management
RSI + Position Sizing + Stop Loss + Take Profit
"""
import os, json, time, requests, hmac, hashlib, logging
from dotenv import load_dotenv
from risk_manager import RiskManager

load_dotenv('/root/btbot/.env')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('/root/btbot/btbot_v5.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

API_KEY = os.getenv('BINANCE_API_KEY')
SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
BASE_URL = "https://api.binance.com"
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BTBOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_BTBOT_CHAT_ID')
PAIRS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']

# Initialize Risk Manager
risk_mgr = RiskManager(
    account_balance=5000,     # Conservative for BTBOT
    risk_per_trade=0.5,       # 0.5% per trade
    max_drawdown=3.0,         # 3% max daily loss
    position_limit=3,
    stop_loss_pct=1.5,        # Tighter stops for RSI
    take_profit_pct=2.5
)

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
            return r.json()
        return None
    except:
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
            rsi = 100 - (100 / (1 + rs)) if rs else 50
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
        
        signal = None
        if rsi < 25:
            signal = {'symbol': symbol, 'action': 'BUY', 'price': price, 'rsi': rsi, 'strength': 'EXTREME'}
        elif rsi < 35:
            signal = {'symbol': symbol, 'action': 'BUY', 'price': price, 'rsi': rsi, 'strength': 'STRONG'}
        elif rsi > 75:
            signal = {'symbol': symbol, 'action': 'SELL', 'price': price, 'rsi': rsi, 'strength': 'EXTREME'}
        elif rsi > 65:
            signal = {'symbol': symbol, 'action': 'SELL', 'price': price, 'rsi': rsi, 'strength': 'STRONG'}
        
        return signal
    except:
        return None

def main():
    logger.info("🚀 BTBOT v5.0 - WITH RISK MANAGEMENT")
    logger.info("🔗 Mode: LIVE | Risk: 0.5% per trade | Max Loss: 3% daily")
    cycle = 0
    
    while True:
        cycle += 1
        try:
            acct = get_account()
            if not acct:
                time.sleep(60)
                continue
            
            logger.info(f"⏱️ BTBOT cycle {cycle}: checking {len(PAIRS)} pairs")
            
            # Check exits
            for symbol in PAIRS:
                price = get_price(symbol)
                if price:
                    exit_signal = risk_mgr.check_position(symbol, price)
                    if exit_signal:
                        msg = f"🟠 BTBOT v5 - EXIT\n"
                        msg += f"  {exit_signal['action']}\n"
                        msg += f"  {symbol} @ ${exit_signal['exit_price']:.2f}\n"
                        msg += f"  P&L: ${exit_signal['pnl']:.2f} ({exit_signal['pnl_pct']:+.2f}%)"
                        send_telegram(msg)
            
            # Generate signals
            signals = [generate_signal(p) for p in PAIRS]
            signals = [s for s in signals if s]
            
            if signals:
                msg = f"🟠 BTBOT v5 - {len(signals)} SIGNALS (RSI + RISK MGT)\n"
                for s in signals[:5]:
                    can_open, reason = risk_mgr.can_open_position()
                    
                    if can_open:
                        stop_price = s['price'] * (1 - 0.015)
                        qty = risk_mgr.get_position_size(s['price'], stop_price)
                        success, result = risk_mgr.open_position(s['symbol'], s['price'], qty)
                        
                        if success:
                            msg += f"\n  {s['symbol']}: {s['action']} @ ${s['price']:.2f}\n"
                            msg += f"    Size: {qty:.4f} | Stop: ${result['stop']:.2f} | Target: ${result['target']:.2f}\n"
                            msg += f"    RSI: {s['rsi']:.1f} ({s['strength']})"
                
                status = risk_mgr.get_status()
                msg += f"\n\n📊 Status: {status['open_positions']}/{status['max_positions']} | Daily P&L: ${status['daily_pnl']:.2f}"
                send_telegram(msg)
            
            time.sleep(60)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
