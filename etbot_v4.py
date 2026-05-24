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

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=5)
        logger.info(f"✉️ Telegram sent: {len(msg)} chars")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def get_crypto_data(coin_id):
    """Get crypto data from CoinGecko"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if coin_id in data:
                coin_data = data[coin_id]
                return {
                    'price': coin_data.get('usd', 0),
                    'change': coin_data.get('usd_24h_change', 0)
                }
        return None
    except Exception as e:
        logger.debug(f"CoinGecko error for {coin_id}: {e}")
        return None

def generate_signal(symbol, coin_id):
    """Generate trading signal based on 24h change"""
    try:
        data = get_crypto_data(coin_id)
        if not data:
            return None
        
        price = data.get('price', 0)
        change = data.get('change', 0)
        
        if price <= 0:
            return None
        
        if change > 8:  # Strong uptrend
            return {'symbol': symbol, 'action': 'BUY', 'price': price, 'change': change, 'strength': 'STRONG'}
        elif change > 4:  # Moderate uptrend
            return {'symbol': symbol, 'action': 'BUY', 'price': price, 'change': change, 'strength': 'MEDIUM'}
        elif change < -8:  # Strong downtrend
            return {'symbol': symbol, 'action': 'SELL', 'price': price, 'change': change, 'strength': 'STRONG'}
        elif change < -4:  # Moderate downtrend
            return {'symbol': symbol, 'action': 'SELL', 'price': price, 'change': change, 'strength': 'MEDIUM'}
        
        return None
    except Exception as e:
        logger.error(f"Signal error for {symbol}: {e}")
        return None

def main():
    logger.info("🚀 ETBOT v4.0 - SIMPLIFIED REST API")
    symbols = [('BTC', 'bitcoin'), ('ETH', 'ethereum')]
    cycle = 0
    
    while True:
        cycle += 1
        try:
            logger.info(f"⏱️ ETBOT cycle {cycle}: checking {len(symbols)} symbols")
            signals = []
            for symbol, coin_id in symbols:
                sig = generate_signal(symbol, coin_id)
                if sig:
                    signals.append(sig)
                    logger.info(f"Signal found: {sig}")
            
            if signals:
                msg = f"🔵 ETBOT v4 - {len(signals)} signals detected\n"
                for s in signals[:5]:
                    msg += f"  {s['symbol']}: {s['action']} @ ${s['price']:.2f} ({s['change']:+.2f}%)\n"
                send_telegram(msg)
            
            time.sleep(60)
        except Exception as e:
            logger.error(f"Loop error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
