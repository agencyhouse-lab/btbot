#!/usr/bin/env python3
"""
🔵 ETBOT v5.0 - Crypto Watch with Risk Management
Conservative position sizing
"""
import os, json, time, requests, logging
from dotenv import load_dotenv
from risk_manager import RiskManager

load_dotenv('/root/btbot/.env')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', handlers=[logging.FileHandler('/root/btbot/etbot_v5.log'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_ETBOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_ETBOT_CHAT_ID')

risk_mgr = RiskManager(
    account_balance=3000,
    risk_per_trade=0.3,
    max_drawdown=2.0,
    position_limit=2,
    stop_loss_pct=3.0,
    take_profit_pct=5.0
)

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg}, timeout=5)
        logger.info(f"✉️ Telegram sent: {len(msg)} chars")
    except Exception as e:
        logger.error(f"Telegram error: {e}")

def get_crypto_data(coin_id):
    """Get crypto data from CoinGecko - with error handling"""
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if coin_id in data:
                coin_data = data[coin_id]
                price = coin_data.get('usd', 0)
                change = coin_data.get('usd_24h_change', 0)
                if price > 0:
                    return {'price': price, 'change': change}
        return None
    except Exception as e:
        logger.debug(f"CoinGecko error for {coin_id}: {e}")
        return None

def generate_signal(symbol, coin_id):
    """Generate trading signal based on 24h change"""
    try:
        data = get_crypto_data(coin_id)
        if not data:  # FIX: Check if data is None before using .get()
            return None
        
        price = data.get('price', 0)
        change = data.get('change', 0)
        
        if price <= 0:
            return None
        
        signal = None
        if change > 8:
            signal = {'symbol': symbol, 'action': 'BUY', 'price': price, 'change': change, 'strength': 'STRONG'}
        elif change > 4:
            signal = {'symbol': symbol, 'action': 'BUY', 'price': price, 'change': change, 'strength': 'MEDIUM'}
        elif change < -8:
            signal = {'symbol': symbol, 'action': 'SELL', 'price': price, 'change': change, 'strength': 'STRONG'}
        elif change < -4:
            signal = {'symbol': symbol, 'action': 'SELL', 'price': price, 'change': change, 'strength': 'MEDIUM'}
        
        return signal
    except Exception as e:
        logger.error(f"Signal error for {symbol}: {e}")
        return None

def main():
    logger.info("🚀 ETBOT v5.0 - WITH RISK MANAGEMENT")
    logger.info("🔗 Mode: Watch | Risk: 0.3% per trade | Max Loss: 2% daily")
    symbols = [('BTC', 'bitcoin'), ('ETH', 'ethereum')]
    cycle = 0
    
    while True:
        cycle += 1
        try:
            logger.info(f"⏱️ ETBOT cycle {cycle}: checking crypto")
            
            # Check exits - FIX: Safe check for positions
            for symbol, coin_id in symbols:
                try:
                    data = get_crypto_data(coin_id)
                    if data:
                        price = data.get('price')
                        if price and symbol in risk_mgr.open_positions:
                            exit_signal = risk_mgr.check_position(symbol, price)
                            if exit_signal:
                                msg = f"🔵 ETBOT v5 - EXIT\n{exit_signal['action']}\n{symbol} @ ${exit_signal['exit_price']:.2f}\nP&L: ${exit_signal['pnl']:.2f}"
                                send_telegram(msg)
                except Exception as e:

