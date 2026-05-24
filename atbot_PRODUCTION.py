#!/usr/bin/env python3
"""
🤖 ATBOT v3.0 - PRODUCTION LIVE TRADING BOT
Live Alpaca Account Trading
Two Separate Bots - THIS IS LIVE TRADING BOT
"""

import logging
import time
import json
import requests
from datetime import datetime
import alpaca_trade_api as tradeapi

# ==================== LOGGING ====================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/trading_bot/atbot.log'),
        logging.StreamHandler()
    ]
)

# ==================== LIVE ALPACA CREDENTIALS ====================
LIVE_API_KEY = "AKUA74O5IDW4EY6PZ47R6NJ6CY"
LIVE_API_SECRET = "AmP75SqGjbfX7a9ZPsRqWkAuv7HWWDf7jkbYqhid5y5z"
LIVE_BASE_URL = "https://api.alpaca.markets"

# ==================== ATBOT TELEGRAM ====================
ATBOT_TELEGRAM_TOKEN = "8924056219:AAE3as-NwRVFRnaA8GOO1DmXGm7CU1S5sJQ"
CHAT_ID = 5587885687

# ==================== TRADING CONFIG ====================
CURRENT_MODE = "🔴 LIVE REAL TRADING"
RISK_PER_TRADE = 0.0025  # 0.25% of buying power
MIN_STOP_LOSS = 0.005    # 0.5%
MIN_SIGNAL_STRENGTH = 0.80  # Conservative
MAX_OPEN_TRADES = 5
SCAN_INTERVAL = 30  # seconds
CHECK_EXIT_INTERVAL = 15  # seconds

# ==================== MARKETS ====================
STOCKS = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
ETFS = ["SPY", "QQQ", "IWM", "DIA"]
ALL_SYMBOLS = STOCKS + ETFS

# ==================== GLOBAL STATE ====================
open_trades = {}
trade_history = []
last_hourly_report = 0
last_account_data = {}
api = None

def init_api():
    global api
    try:
        api = tradeapi.REST(LIVE_API_KEY, LIVE_API_SECRET, LIVE_BASE_URL, api_version='v2')
        logging.info(f"✅ ATBOT: Alpaca Live API connected")
        return True
    except Exception as e:
        logging.error(f"❌ ATBOT: API connection failed: {e}")
        return False

def send_telegram(message):
    """Send message to ATBOT Telegram"""
    try:
        url = f"https://api.telegram.org/bot{ATBOT_TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            logging.info(f"✉️ ATBOT Telegram sent")
            return True
        return False
    except Exception as e:
        logging.warning(f"⚠️ ATBOT Telegram error: {e}")
        return False

def get_account_info():
    """Get REAL account info from Alpaca"""
    try:
        account = api.get_account()
        data = {
            "equity": float(account.equity),
            "portfolio_value": float(account.portfolio_value),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "timestamp": datetime.now().isoformat()
        }
        logging.info(f"💰 ATBOT Account: Equity=${data['equity']:.2f} | BP=${data['buying_power']:.2f}")
        return data
    except Exception as e:
        logging.error(f"❌ ATBOT Account error: {e}")
        return None

def save_state():
    """Save trading state"""
    try:
        state = {
            "open_trades": open_trades,
            "trade_history": trade_history,
            "last_account_data": last_account_data,
            "timestamp": datetime.now().isoformat()
        }
        with open('/root/trading_bot/atbot_state.json', 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logging.error(f"Save state error: {e}")

def load_state():
    """Load trading state"""
    global open_trades, trade_history, last_account_data
    try:
        with open('/root/trading_bot/atbot_state.json', 'r') as f:
            state = json.load(f)
            open_trades = state.get("open_trades", {})
            trade_history = state.get("trade_history", [])
            last_account_data = state.get("last_account_data", {})
            logging.info(f"✅ ATBOT State loaded: {len(trade_history)} trades")
    except Exception as e:
        logging.info(f"ℹ️ ATBOT Starting fresh state")
        save_state()

def get_market_data(symbol):
    """Fetch 1-minute bars for signal detection"""
    try:
        bars = api.get_bars(symbol, "1Min", limit=100).df
        if bars is None or bars.empty:
            logging.debug(f"⚠️ No bars for {symbol}")
            return None
        
        close_prices = bars['close'].values
        if len(close_prices) < 20:
            return None
            
        return {
            "current_price": float(close_prices[-1]),
            "high": float(bars['high'].max()),
            "low": float(bars['low'].min()),
            "volume": float(bars['volume'].sum()),
            "bars": close_prices
        }
    except Exception as e:
        logging.debug(f"Market data error {symbol}: {e}")
        return None

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    try:
        if len(prices) < period + 1:
            return 50
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [abs(d) if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period if period > 0 else 0
        avg_loss = sum(losses) / period if period > 0 else 0
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logging.debug(f"RSI error: {e}")
        return 50

def detect_signal(symbol, market_data):
    """Detect trading signals"""
    try:
        if not market_data or "bars" not in market_data:
            return None
        
        prices = market_data["bars"]
        current_price = prices[-1]
        rsi = calculate_rsi(prices)
        
        # Signal 1: RSI Oversold (very strong)
        if rsi < 35:
            strength = min(0.98, 0.85 + (35 - rsi) / 100)
            return {
                "signal": True,
                "strength": strength,
                "reason": f"RSI Oversold: {rsi:.0f}",
                "profit_target": 0.025
            }
        
        # Signal 2: SMA Crossover (strong)
        if len(prices) >= 20:
            sma_20 = sum(prices[-20:]) / 20
            if current_price > sma_20 and rsi > 50 and rsi < 70:
                strength = min(0.95, 0.80 + (rsi - 50) / 100)
                return {
                    "signal": True,
                    "strength": strength,
                    "reason": f"SMA Cross RSI: {rsi:.0f}",
                    "profit_target": 0.020
                }
        
        return None
    except Exception as e:
        logging.debug(f"Signal detect error {symbol}: {e}")
        return None

def calculate_position_size(entry_price, stop_loss_price, available_buying_power):
    """Calculate position size based on risk"""
    try:
        if available_buying_power <= 0 or entry_price <= 0:
            return 0
        
        risk_amount = available_buying_power * RISK_PER_TRADE
        risk_per_unit = entry_price - stop_loss_price
        
        if risk_per_unit <= 0:
            return 0
        
        position_size = int(risk_amount / risk_per_unit)
        
        # Ensure we can afford it
        cost = entry_price * position_size
        if cost > available_buying_power * 0.95:
            position_size = int((available_buying_power * 0.95) / entry_price)
        
        return max(1, position_size)
    except Exception as e:
        logging.error(f"Position size error: {e}")
        return 0

def execute_buy_order(symbol, signal_strength, signal_info):
    """Execute buy order"""
    global open_trades, last_account_data
    
    if len(open_trades) >= MAX_OPEN_TRADES:
        return False
    
    if symbol in open_trades:
        return False
    
    try:
        account = get_account_info()
        if not account or account["buying_power"] <= 10:
            logging.warning(f"⚠️ ATBOT: Insufficient buying power (${account['buying_power']:.2f})")
            return False
        
        last_account_data = account
        
        market_data = get_market_data(symbol)
        if not market_data:
            return False
        
        current_price = market_data["current_price"]
        stop_loss_price = current_price * (1 - MIN_STOP_LOSS)
        take_profit_price = current_price * (1 + signal_info.get("profit_target", 0.020))
        
        shares = calculate_position_size(current_price, stop_loss_price, account["buying_power"])
        
        if shares < 1:
            logging.warning(f"⚠️ ATBOT {symbol}: Cannot calculate position (price ${current_price:.2f}, BP ${account['buying_power']:.2f})")
            return False
        
        # Try to place order
        try:
            order = api.submit_order(
                symbol=symbol,
                qty=shares,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            
            open_trades[symbol] = {
                "entry_price": current_price,
                "shares": shares,
                "stop_loss": stop_loss_price,
                "take_profit": take_profit_price,
                "signal_strength": signal_strength,
                "entry_time": datetime.now().isoformat(),
                "order_id": order.id,
                "reason": signal_info.get("reason", "")
            }
            
            save_state()
            
            msg = f"""🟢 <b>BUY EXECUTED</b>
━━━━━━━━━━━━━━━━
📊 {symbol} | Signal: {signal_strength*100:.0f}%
💰 ${current_price:.4f} x {shares}
⛔ SL: ${stop_loss_price:.4f}
🎁 TP: ${take_profit_price:.4f}
💵 Value: ${current_price*shares:.2f}
🤖 <b>LIVE TRADING</b> 🔴"""
            
            send_telegram(msg)
            logging.info(f"🟢 ATBOT BUY: {symbol} @ ${current_price:.4f} x{shares}")
            return True
            
        except Exception as order_error:
            logging.error(f"❌ ATBOT Order failed {symbol}: {order_error}")
            send_telegram(f"❌ ATBOT Order failed: {symbol}\nError: {str(order_error)[:100]}")
            return False
    
    except Exception as e:
        logging.error(f"❌ ATBOT Buy error: {e}")
        return False

def check_exit_signals():
    """Check for exit signals"""
    for symbol in list(open_trades.keys()):
        try:
            market_data = get_market_data(symbol)
            if not market_data:
                continue
            
            current_price = market_data["current_price"]
            trade = open_trades[symbol]
            
            if current_price <= trade["stop_loss"]:
                execute_sell_order(symbol, "STOP LOSS", current_price)
            elif current_price >= trade["take_profit"]:
                execute_sell_order(symbol, "TAKE PROFIT", current_price)
        except Exception as e:
            logging.error(f"Exit check error {symbol}: {e}")

def execute_sell_order(symbol, exit_reason, exit_price):
    """Execute sell order"""
    global open_trades
    
    if symbol not in open_trades:
        return False
    
    try:
        trade = open_trades[symbol]
        shares = int(trade["shares"])
        entry_price = trade["entry_price"]
        
        try:
            order = api.submit_order(
                symbol=symbol,
                qty=shares,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            
            pnl = (exit_price - entry_price) * shares
            pnl_pct = ((exit_price - entry_price) / entry_price) * 100
            
            del open_trades[symbol]
            
            trade_history.append({
                "symbol": symbol,
                "entry": entry_price,
                "exit": exit_price,
                "shares": shares,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "reason": exit_reason,
                "timestamp": datetime.now().isoformat()
            })
            
            save_state()
            
            emoji = "✅" if pnl > 0 else "❌"
            color = "🟢" if pnl > 0 else "🔴"
            
            msg = f"""{color} <b>{emoji} CLOSED</b>
━━━━━━━━━━━━━━━━
📊 {symbol} | {exit_reason}
📥 Entry: ${entry_price:.4f}
📤 Exit: ${exit_price:.4f}
💵 P&L: <b>${pnl:+.2f}</b> ({pnl_pct:+.1f}%)
🤖 <b>LIVE TRADING</b> 🔴"""
            
            send_telegram(msg)
            logging.info(f"{color} ATBOT EXIT: {symbol} {emoji} P&L: ${pnl:+.2f}")
            return True
        except Exception as e:
            logging.error(f"❌ ATBOT Sell error: {e}")
            return False
    
    except Exception as e:
        logging.error(f"❌ ATBOT Exit error: {e}")
        return False

def send_hourly_report():
    """Send hourly summary"""
    global last_hourly_report, last_account_data
    
    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    if last_hourly_report == current_hour.timestamp():
        return
    
    last_hourly_report = current_hour.timestamp()
    
    try:
        account = get_account_info()
        if not account:
            return
        
        last_account_data = account
        
        total = len(trade_history)
        wins = sum(1 for t in trade_history if t.get("pnl", 0) > 0)
        losses = total - wins
        win_rate = (wins / total * 100) if total > 0 else 0
        total_pnl = sum(t.get("pnl", 0) for t in trade_history)
        
        open_pos = "\n🔴 <b>OPEN:</b>\n"
        if open_trades:
            for sym, trade in open_trades.items():
                open_pos += f"  {sym}: {trade['shares']} @ ${trade['entry_price']:.4f}\n"
        else:
            open_pos = ""
        
        msg = f"""📊 <b>HOURLY REPORT</b>
━━━━━━━━━━━━━━━━━━━━
⏰ {datetime.now().strftime('%H:%M:%S')}
🤖 <b>LIVE TRADING</b> 🔴

💰 <b>ACCOUNT:</b>
  Equity: ${account['equity']:,.2f}
  Buying Power: ${account['buying_power']:,.2f}
  Cash: ${account['cash']:,.2f}

📈 <b>TRADES:</b>
  Total: {total} | ✅ {wins} | ❌ {losses}
  Win Rate: {win_rate:.0f}%
  P&L: <b>${total_pnl:+,.2f}</b>
{open_pos}"""
        
        send_telegram(msg)
        save_state()
        logging.info(f"📊 ATBOT Hourly report sent")
    except Exception as e:
        logging.error(f"Hourly report error: {e}")

def scan_markets():
    """Scan all symbols for trading signals"""
    logging.info(f"🔍 ATBOT Scanning {len(ALL_SYMBOLS)} symbols...")
    
    account = get_account_info()
    if not account:
        return
    
    if account["buying_power"] < 10:
        logging.warning(f"⚠️ ATBOT: Low buying power ${account['buying_power']:.2f}")
        return
    
    signals = []
    
    for symbol in ALL_SYMBOLS:
        if symbol in open_trades:
            continue
        
        try:
            market_data = get_market_data(symbol)
            if not market_data:
                continue
            
            signal_info = detect_signal(symbol, market_data)
            
            if signal_info and signal_info.get("signal"):
                if signal_info.get("strength", 0) >= MIN_SIGNAL_STRENGTH:
                    signals.append({
                        "symbol": symbol,
                        "strength": signal_info.get("strength", 0),
                        "info": signal_info
                    })
                    logging.info(f"💡 ATBOT {symbol}: Signal {signal_info.get('strength', 0)*100:.0f}%")
        
        except Exception as e:
            logging.debug(f"Scan error {symbol}: {e}")
    
    # Execute top signals
    signals.sort(key=lambda x: x["strength"], reverse=True)
    available_slots = MAX_OPEN_TRADES - len(open_trades)
    
    for signal in signals[:available_slots]:
        execute_buy_order(signal["symbol"], signal["strength"], signal["info"])
    
    if not signals:
        logging.info(f"⏳ ATBOT: No 80%+ signals found")

def main_loop():
    """Main trading loop"""
    global api
    
    logging.info("="*80)
    logging.info("🚀 ATBOT v3.0 PRODUCTION - LIVE TRADING")
    logging.info("="*80)
    
    if not init_api():
        send_telegram("🚨 ATBOT: API connection failed!")
        return
    
    load_state()
    
    try:
        account = get_account_info()
        if not account:
            raise Exception("Cannot get account")
        
        logging.info(f"✅ ATBOT Connected: ${account['equity']:,.2f}")
        
        send_telegram(f"""✅ <b>ATBOT v3.0 STARTED</b>
━━━━━━━━━━━━━━━━━━
🤖 <b>LIVE TRADING</b> 🔴
💰 Equity: ${account['equity']:,.2f}
📊 Buying Power: ${account['buying_power']:,.2f}
⛔ Risk: 0.25% per trade
🎯 Max Trades: 5
📱 Signal: 80%+ confidence
━━━━━━━━━━━━━━━━━━
🚀 Trading started!""")
    
    except Exception as e:
        logging.error(f"❌ ATBOT startup error: {e}")
        send_telegram(f"🚨 ATBOT Error: {e}")
        return
    
    scan_counter = 0
    exit_counter = 0
    
    while True:
        try:
            exit_counter += 1
            scan_counter += 1
            
            # Check exits every 15 seconds
            if exit_counter % (CHECK_EXIT_INTERVAL // SCAN_INTERVAL) == 0:
                check_exit_signals()
            
            # Scan every 30 seconds (4 x 30 = 120 seconds = 2 minutes)
            if scan_counter >= 4:
                scan_markets()
                scan_counter = 0
            
            # Hourly report
            if datetime.now().minute == 0 and datetime.now().second < 30:
                send_hourly_report()
            
            time.sleep(SCAN_INTERVAL)
        
        except KeyboardInterrupt:
            logging.info("👋 ATBOT stopped")
            send_telegram("👋 ATBOT stopped")
            break
        
        except Exception as e:
            logging.error(f"❌ ATBOT loop error: {e}")
            time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main_loop()

