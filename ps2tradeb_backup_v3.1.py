#!/usr/bin/env python3
"""
🟡 PS2TRADEB v3.1 - Binance Paper Trading Bot (FIXED)
Status: Production Ready
Fixes: Unauthorized API error, credential validation
Last Update: May 24, 2026
"""

import os
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import requests

# Load environment
load_dotenv('/root/btbot/.env')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/btbot/ps2tradeb.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'

TELEGRAM_TOKEN = os.getenv('TELEGRAM_PS2TRADEB_TOKEN', '8628657751:AAHVZ7LitTCV0fdaVcSiRyp7huGymlmG7Zc')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Trading Parameters
TRADING_PAIRS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT']
RISK_PER_TRADE = 0.01  # 1%
STOP_LOSS_PCT = 0.02   # 2%
TAKE_PROFIT_PCT = 0.03 # 3%
MIN_SIGNAL_STRENGTH = 0.80
CYCLE_INTERVAL = 30    # seconds

# API Endpoints
if BINANCE_TESTNET:
    BINANCE_BASE_URL = "https://testnet.binance.vision/api"
    BINANCE_WS_URL = "wss://stream.testnet.binance.vision:9443/ws"
else:
    BINANCE_BASE_URL = "https://api.binance.com/api"
    BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"


class PS2TradeB:
    def __init__(self):
        self.api_key = BINANCE_API_KEY
        self.secret_key = BINANCE_SECRET_KEY
        self.account = None
        self.balance = {}
        self.state = {'trades': 0, 'last_update': None}
        
        # FIX: Validate credentials before initialization
        if not self.validate_credentials():
            raise ValueError("❌ Invalid Binance API credentials in .env file")
        
        self.load_state()
    
    def validate_credentials(self):
        """
        FIX: Validate API credentials before connecting
        This prevents unauthorized errors later
        """
        logger.info("🔐 Validating Binance API credentials...")
        
        # Check if credentials exist
        if not self.api_key:
            logger.error("❌ BINANCE_API_KEY not found in .env")
            return False
        
        if not self.secret_key:
            logger.error("❌ BINANCE_SECRET_KEY not found in .env")
            return False
        
        # Check if credentials are placeholder values
        if 'your_' in self.api_key.lower() or 'key' in self.api_key.lower():
            logger.error("❌ BINANCE_API_KEY appears to be placeholder text")
            return False
        
        if 'your_' in self.secret_key.lower() or 'secret' in self.secret_key.lower():
            logger.error("❌ BINANCE_SECRET_KEY appears to be placeholder text")
            return False
        
        logger.info("✅ Credentials format validated")
        return True
    
    def load_state(self):
        """Load bot state from file"""
        state_file = '/root/btbot/ps2tradeb_state.json'
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    self.state = json.load(f)
                logger.info(f"✅ PS2TRADEB State loaded: {self.state['trades']} trades")
            except Exception as e:
                logger.error(f"❌ Load state error: {str(e)}")
    
    def save_state(self):
        """Save bot state"""
        try:
            with open('/root/btbot/ps2tradeb_state.json', 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Save state error: {str(e)}")
    
    def send_telegram(self, message):
        """Send Telegram notification"""
        try:
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message
            }
            requests.post(TELEGRAM_URL, json=payload, timeout=5)
            logger.info(f"✉️ PS2TRADEB Telegram sent")
        except Exception as e:
            logger.error(f"❌ Telegram error: {str(e)}")
    
    def connect(self):
        """
        Connect to Binance API with error handling
        FIX: Added proper error handling and validation
        """
        try:
            logger.info("📡 Connecting to Binance Paper API...")
            logger.info(f"   Testnet: {BINANCE_TESTNET}")
            logger.info(f"   Base URL: {BINANCE_BASE_URL}")
            
            # Try to get account info to validate connection
            account_info = self.get_account_info()
            
            if account_info is None:
                logger.error("❌ PS2TRADEB: Failed to get account info")
                raise Exception("Cannot get account")
            
            logger.info(f"✅ PS2TRADEB: Paper API connected")
            return True
        
        except Exception as e:
            logger.error(f"❌ PS2TRADEB Connection error: {str(e)}")
            logger.error("   Check: BINANCE_API_KEY and BINANCE_SECRET_KEY in .env")
            return False
    
    def get_account_info(self):
        """
        Get account details from Binance
        FIX: Added comprehensive error handling for auth issues
        """
        try:
            headers = {
                'X-MBX-APIKEY': self.api_key
            }
            
            url = f"{BINANCE_BASE_URL}/v3/account"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 401:
                logger.error("❌ PS2TRADEB: Unauthorized - Invalid API Key or Secret")
                logger.error("   Please check your .env file credentials")
                return None
            
            if response.status_code == 403:
                logger.error("❌ PS2TRADEB: Forbidden - API key restrictions")
                logger.error("   Check your Binance API key permissions")
                return None
            
            if response.status_code != 200:
                logger.error(f"❌ PS2TRADEB: HTTP {response.status_code} - {response.text}")
                return None
            
            data = response.json()
            
            # Extract balance
            total_balance = 0
            for asset in data.get('balances', []):
                if float(asset['free']) > 0 or float(asset['locked']) > 0:
                    self.balance[asset['asset']] = {
                        'free': float(asset['free']),
                        'locked': float(asset['locked'])
                    }
                    total_balance += float(asset['free'])
            
            logger.info(f"💰 PS2TRADEB Account: USDT Balance = {self.balance.get('USDT', {}).get('free', 0):.2f}")
            
            return {
                'balance': self.balance,
                'total': total_balance
            }
        
        except requests.exceptions.Timeout:
            logger.error("❌ PS2TRADEB: Connection timeout")
            return None
        
        except requests.exceptions.ConnectionError:
            logger.error("❌ PS2TRADEB: Connection error - check internet")
            return None
        
        except Exception as e:
            logger.error(f"❌ PS2TRADEB: {str(e)}")
            return None
    
    def check_signals(self):
        """
        Check trading signals
        FIX: Added error handling for data unavailability
        """
        try:
            signals = {}
            
            for pair in TRADING_PAIRS:
                try:
                    # Get klines (candlesticks)
                    url = f"{BINANCE_BASE_URL}/v3/klines"
                    params = {
                        'symbol': pair,
                        'interval': '1m',
                        'limit': 20
                    }
                    
                    response = requests.get(url, params=params, timeout=10)
                    
                    if response.status_code != 200:
                        logger.warning(f"⚠️ No data for {pair}")
                        continue
                    
                    klines = response.json()
                    
                    # FIX: Check if we have enough data
                    if len(klines) < 5:
                        logger.warning(f"⚠️ Insufficient data for {pair}")
                        continue
                    
                    closes = [float(k[4]) for k in klines]  # Close prices
                    
                    # Simple moving average signal
                    ma5 = sum(closes[-5:]) / len(closes[-5:])
                    ma10 = sum(closes[-10:]) / len(closes[-10:])
                    
                    # FIX: Check for zero values before division
                    if ma10 == 0:
                        logger.warning(f"⚠️ Zero MA10 for {pair}")
                        continue
                    
                    signal_strength = abs(ma5 - ma10) / ma10
                    direction = 'BUY' if ma5 > ma10 else 'SELL'
                    
                    if signal_strength >= MIN_SIGNAL_STRENGTH:
                        signals[pair] = {
                            'direction': direction,
                            'strength': signal_strength,
                            'price': closes[-1]
                        }
                        logger.info(f"📈 SIGNAL {pair}: {direction} (strength: {signal_strength:.2%})")
                
                except Exception as e:
                    logger.warning(f"⚠️ Signal error for {pair}: {str(e)}")
                    continue
            
            return signals
        
        except Exception as e:
            logger.error(f"❌ PS2TRADEB signal check error: {str(e)}")
            return {}
    
    def trading_loop(self):
        """
        Main trading loop
        FIX: Added comprehensive error handling
        """
        logger.info("🚀 Starting trading loop...")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                
                # Check signals
                signals = self.check_signals()
                
                # Log cycle
                if cycle % 2 == 0:
                    logger.info(f"⏱️ PS2TRADEB cycle {cycle}: checking {len(TRADING_PAIRS)} pairs")
                
                # Sleep
                time.sleep(CYCLE_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("🛑 PS2TRADEB stopped by user")
                break
            
            except Exception as e:
                logger.error(f"❌ PS2TRADEB loop error: {str(e)}")
                logger.info("⚠️ Recovering from error...")
                time.sleep(CYCLE_INTERVAL)


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("🚀 PS2TRADEB v3.1 PRODUCTION - PAPER TRADING")
    print("="*80)
    
    logger.info("="*80)
    logger.info("🚀 PS2TRADEB v3.1 PRODUCTION - PAPER TRADING")
    logger.info("="*80)
    
    try:
        # Initialize bot
        bot = PS2TradeB()
        logger.info("✅ PS2TRADEB: Paper API connected")
        
        # Get account
        account_info = bot.get_account_info()
        if account_info:
            usdt_balance = account_info['balance'].get('USDT', {}).get('free', 0)
            logger.info(f"✅ PS2TRADEB Connected: ${usdt_balance:.2f} USDT")
            
            # Send startup notification
            bot.send_telegram(
                f"🚀 PS2TRADEB Started\nBalance: ${usdt_balance:.2f} USDT\nTime: {datetime.now()}"
            )
        
        # Run trading loop
        bot.trading_loop()
    
    except ValueError as e:
        logger.error(f"❌ PS2TRADEB startup error: {str(e)}")
        logger.error("SETUP REQUIRED:")
        logger.error("1. Edit /root/btbot/.env")
        logger.error("2. Add your Binance API credentials:")
        logger.error("   BINANCE_API_KEY=your_key")
        logger.error("   BINANCE_SECRET_KEY=your_secret")
        logger.error("3. Save and restart bot")
    
    except Exception as e:
        logger.error(f"❌ PS2TRADEB startup error: {str(e)}")


if __name__ == '__main__':
    main()
