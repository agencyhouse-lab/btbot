#!/usr/bin/env python3
"""
🔵 ETBOT v4.0 - Simplified eToro Trading Bot
Direct REST API approach
"""
import os, json, time, requests, logging
from dotenv import load_dotenv

load_dotenv('/root/btbot/.env')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('/root/btbot/etbot_v4.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_ETBOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_ETBOT_CHAT_ID')
SYMBOLS = ['BTC', 'ETH', 'SPY', 'AAPL', 'GOOGL']

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=5)
        logger.info(f"✉️ Telegram sent: {len(msg)} chars")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def get_crypto_price(symbol):
    """Get price from CoinGecko (free API)"""
    try:
        if symbol.upper() == 'BTC':
            symbol = 'bitcoin'
        elif symbol.upper() == 'ETH':
            symbol = 'ethereum'
        
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if symbol in data:
                return data[symbol]
        return None
    except Exception as e:
        logger.warning(f"Price error for {symbol}: {e}")
        return None

def get_stock_price(symbol):
    """Get stock price from Yahoo Finance"""
    try:
        import yfinance as yf
        ticker = yf.Ticker(symbol)
        data = ticker.history(period='1d')
        if len(data) > 0:
            return {'price': data['Close'].iloc[-1], 'change': ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0] * 100)}
        return None
    except:
        return None

def generate_signal(symbol):
    """Generate trading signal"""
    try:
        if symbol.upper() in ['BTC', 'ETH']:
            data = get_crypto_price(symbol)
            if data and f"{symbol.lower()}" in str(data):
                price = data.get(symbol.lower().replace('btc', 'bitcoin').replace('eth', 'ethereum'), {}).get('usd', 0)
                change = data.get(symbol.lower().replace('btc', 'bitcoin').replace('eth', 'ethereum'), {}).get('usd_24h_change', 0)
                if price > 0:
                    if change > 5:
                        return {'symbol': symbol, 'action': 'BUY', 'price': price, 'change': change}
                    elif change < -5:
                        return {'symbol': symbol, 'action': 'SELL', 'price': price, 'change': change}
        return None
    except Exception as e:
        logger.error(f"Signal error for {symbol}: {e}")
        return None

def main():
    logger.info("🚀 ETBOT v4.0 - SIMPLIFIED REST API")
    cycle = 0
    while True:
        cycle += 1
        try:
            logger.info(f"⏱️ ETBOT cycle {cycle}: checking {len(SYMBOLS)} symbols")
            signals = [generate_signal(s) for s in SYMBOLS]
            signals = [s for s in signals if s]
            if signals:
                msg = f"🔵 ETBOT v4 - {len(signals)} signals detected\n"
                for s in signals[:5]:
                    msg += f"  {s['symbol']}: {s['action']} @ ${s['price']:.2f}\n"
                send_telegram(msg)
            time.sleep(60)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
