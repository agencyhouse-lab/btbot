#!/usr/bin/env python3
"""
🟠 ATBOT v3.1 - Alpaca Trading Bot (FIXED)
Status: Production Ready
Fixes: Zero-division error in trading loop
Last Update: May 24, 2026
"""

import os
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import requests

# Load environment
load_dotenv('/root/btbot/.env')

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/btbot/atbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.getenv('ALPACA_API_KEY')
SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://api.alpaca.markets')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Trading Parameters
TRADING_SYMBOLS = ['SPY', 'QQQ', 'IWM', 'DIA', 'GLD', 'SLV', 'USO', 'DBC', 'DBA']
RISK_PER_TRADE = 0.01  # 1%
STOP_LOSS_PCT = 0.02   # 2%
TAKE_PROFIT_PCT = 0.03 # 3%
MIN_SIGNAL_STRENGTH = 0.80
CYCLE_INTERVAL = 30  # seconds

class ATBot:
    def __init__(self):
        self.api = None
        self.account = None
        self.state = {'trades': 0, 'last_update': None}
        self.load_state()
        
    def load_state(self):
        """Load bot state from file"""
        state_file = '/root/btbot/atbot_state.json'
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    self.state = json.load(f)
                logger.info(f"✅ ATBOT State loaded: {self.state['trades']} trades")
            except Exception as e:
                logger.error(f"❌ Load state error: {str(e)}")
        
    def save_state(self):
        """Save bot state"""
        try:
            with open('/root/btbot/atbot_state.json', 'w') as f:
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
            logger.info(f"✉️ ATBOT Telegram sent")
        except Exception as e:
            logger.error(f"❌ Telegram error: {str(e)}")
    
    def connect(self):
        """Connect to Alpaca API"""
        try:
            self.api = tradeapi.REST(
                API_KEY,
                SECRET_KEY,
                BASE_URL,
                api_version='v2'
            )
            self.account = self.api.get_account()
            logger.info(f"✅ ATBOT: Alpaca Live API connected")
            return True
        except Exception as e:
            logger.error(f"❌ ATBOT Connection error: {str(e)}")
            return False
    
    def get_account_info(self):
        """Get account details"""
        try:
            account = self.api.get_account()
            equity = float(account.equity)
            buying_power = float(account.buying_power)
            logger.info(f"💰 ATBOT Account: Equity=${equity:.2f} | BP=${buying_power:.2f}")
            return {'equity': equity, 'buying_power': buying_power}
        except Exception as e:
            logger.error(f"❌ ATBOT Account error: {str(e)}")
            return None
    
    def calculate_position_size(self, account_info):
        """
        FIX: Added zero-check validation to prevent division by zero
        Calculate position size based on account equity
        """
        try:
            if account_info is None:
                logger.warning("⚠️ Account info is None, cannot calculate position size")
                return 1  # Default to 1 share
            
            equity = account_info.get('equity', 0)
            
            # FIX: Check for zero equity before division
            if equity <= 0:
                logger.warning(f"⚠️ Invalid equity: ${equity}, using minimum position")
                return 1
            
            # Calculate risk amount
            risk_amount = equity * RISK_PER_TRADE
            
            # Position size = risk amount / stop loss percentage
            # FIX: Added check to prevent division by zero
            if STOP_LOSS_PCT <= 0:
                logger.warning("⚠️ Invalid stop loss %, using minimum position")
                return 1
            
            position_size = int(risk_amount / STOP_LOSS_PCT)
            
            # FIX: Ensure position size is at least 1
            position_size = max(1, position_size)
            
            logger.info(f"📊 Position size: {position_size} shares (Risk: ${risk_amount:.2f})")
            return position_size
            
        except ZeroDivisionError as e:
            logger.error(f"❌ ATBOT: Division by zero - {str(e)}")
            return 1
        except Exception as e:
            logger.error(f"❌ Position calculation error: {str(e)}")
            return 1
    
    def check_signals(self):
        """
        Check trading signals
        FIX: Added error handling for signal calculation
        """
        try:
            signals = {}
            
            for symbol in TRADING_SYMBOLS:
                try:
                    # Get barset data
                    barset = self.api.get_barset(symbol, 'minute', limit=20)
                    
                    if symbol not in barset:
                        logger.warning(f"⚠️ No data for {symbol}")
                        continue
                    
                    bars = barset[symbol]
                    
                    # FIX: Check if we have enough data
                    if len(bars) < 5:
                        logger.warning(f"⚠️ Insufficient data for {symbol}")
                        continue
                    
                    closes = [b.c for b in bars]
                    
                    # Simple moving average signal
                    ma5 = sum(closes[-5:]) / len(closes[-5:])
                    ma10 = sum(closes[-10:]) / len(closes[-10:])
                    
                    # FIX: Check for zero values before division
                    if ma10 == 0:
                        logger.warning(f"⚠️ Zero MA10 for {symbol}")
                        continue
                    
                    signal_strength = abs(ma5 - ma10) / ma10
                    direction = 'BUY' if ma5 > ma10 else 'SELL'
                    
                    if signal_strength >= MIN_SIGNAL_STRENGTH:
                        signals[symbol] = {
                            'direction': direction,
                            'strength': signal_strength,
                            'price': closes[-1]
                        }
                        logger.info(f"📈 SIGNAL {symbol}: {direction} (strength: {signal_strength:.2%})")
                
                except Exception as e:
                    logger.warning(f"⚠️ Signal error for {symbol}: {str(e)}")
                    continue
            
            return signals
        
        except Exception as e:
            logger.error(f"❌ ATBOT signal check error: {str(e)}")
            return {}
    
    def place_trade(self, symbol, signal):
        """Place trade order"""
        try:
            account_info = self.get_account_info()
            qty = self.calculate_position_size(account_info)
            
            side = 'buy' if signal['direction'] == 'BUY' else 'sell'
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            logger.info(f"✅ TRADE: {symbol} {side.upper()} x{qty} @ ${signal['price']:.2f}")
            self.state['trades'] += 1
            self.save_state()
            
            return True
        
        except Exception as e:
            logger.error(f"❌ ATBOT trade error {symbol}: {str(e)}")
            return False
    
    def trading_loop(self):
        """
        Main trading loop
        FIX: Added comprehensive error handling to prevent crashes
        """
        logger.info("🚀 Starting trading loop...")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                
                # Get account info
                account_info = self.get_account_info()
                if account_info is None:
                    logger.warning("⚠️ Cannot get account info, retrying...")
                    time.sleep(CYCLE_INTERVAL)
                    continue
                
                # Check signals
                signals = self.check_signals()
                
                # Place trades on valid signals
                if signals:
                    for symbol, signal in signals.items():
                        self.place_trade(symbol, signal)
                
                # Log cycle
                if cycle % 2 == 0:
                    logger.info(f"⏱️ ATBOT cycle {cycle}: checking {len(TRADING_SYMBOLS)} symbols")
                
                # Sleep
                time.sleep(CYCLE_INTERVAL)
                
            except ZeroDivisionError as e:
                logger.error(f"❌ ATBOT loop error: division by zero - {str(e)}")
                logger.info("⚠️ Continuing after zero-division error...")
                time.sleep(CYCLE_INTERVAL)
            
            except KeyboardInterrupt:
                logger.info("🛑 ATBOT stopped by user")
                break
            
            except Exception as e:
                logger.error(f"❌ ATBOT loop error: {str(e)}")
                logger.info("⚠️ Recovering from error...")
                time.sleep(CYCLE_INTERVAL)


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("🚀 ATBOT v3.1 PRODUCTION - LIVE TRADING")
    print("="*80)
    
    logger.info("="*80)
    logger.info("🚀 ATBOT v3.1 PRODUCTION - LIVE TRADING")
    logger.info("="*80)
    
    bot = ATBot()
    
    # Connect
    if not bot.connect():
        logger.error("❌ ATBOT: Failed to connect to Alpaca")
        return
    
    # Get account
    account_info = bot.get_account_info()
    if account_info:
        logger.info(f"✅ ATBOT Connected: ${account_info['equity']:.2f}")
        
        # Send startup notification
        bot.send_telegram(f"🚀 ATBOT Started\nEquity: ${account_info['equity']:.2f}\nTime: {datetime.now()}")
    
    # Run trading loop
    bot.trading_loop()


if __name__ == '__main__':
    main()
