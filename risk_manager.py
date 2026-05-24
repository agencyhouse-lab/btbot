#!/usr/bin/env python3
"""
🛡️ Risk Manager Module - Protects all trading bots
Position sizing, stop losses, take profits, daily limits
"""
import json
import os
from datetime import datetime, timedelta

class RiskManager:
    def __init__(self, 
                 account_balance=1000,  # USD
                 risk_per_trade=1.0,    # % of account per trade
                 max_drawdown=5.0,      # % max daily loss
                 position_limit=5,      # max open positions
                 stop_loss_pct=2.0,     # % below entry
                 take_profit_pct=3.0):  # % above entry
        
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade  # 1% = $10 on $1000
        self.max_drawdown = max_drawdown       # 5% = $50 max loss
        self.position_limit = position_limit
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Tracking
        self.open_positions = {}
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.today = datetime.now().date()
        self.trades_log = []
        
    def reset_daily_if_needed(self):
        """Reset daily counters at midnight"""
        if datetime.now().date() != self.today:
            self.today = datetime.now().date()
            self.daily_trades = 0
            self.daily_pnl = 0.0
    
    def get_position_size(self, entry_price, stop_price):
        """Calculate position size based on risk per trade"""
        risk_amount = self.account_balance * (self.risk_per_trade / 100)
        risk_per_unit = abs(entry_price - stop_price)
        if risk_per_unit <= 0:
            return 0
        position_size = risk_amount / risk_per_unit
        return position_size
    
    def can_open_position(self):
        """Check if we can open another position"""
        self.reset_daily_if_needed()
        
        # Check daily loss limit
        if self.daily_pnl < -(self.account_balance * self.max_drawdown / 100):
            return False, "Daily loss limit reached"
        
        # Check position limit
        if len(self.open_positions) >= self.position_limit:
            return False, f"Position limit reached ({self.position_limit})"
        
        return True, "OK"
    
    def open_position(self, symbol, entry_price, quantity):
        """Record a new position"""
        can_open, reason = self.can_open_position()
        if not can_open:
            return False, reason
        
        stop_price = entry_price * (1 - self.stop_loss_pct / 100)
        target_price = entry_price * (1 + self.take_profit_pct / 100)
        
        self.open_positions[symbol] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'stop_loss': stop_price,
            'take_profit': target_price,
            'opened_at': datetime.now().isoformat(),
            'status': 'OPEN'
        }
        
        self.daily_trades += 1
        return True, {
            'symbol': symbol,
            'entry': entry_price,
            'stop': stop_price,
            'target': target_price,
            'size': quantity
        }
    
    def check_position(self, symbol, current_price):
        """Check if position hit stop or target"""
        if symbol not in self.open_positions:
            return None
        
        pos = self.open_positions[symbol]
        if pos['status'] != 'OPEN':
            return None
        
        # Check stop loss
        if current_price <= pos['stop_loss']:
            pnl = (current_price - pos['entry_price']) * pos['quantity']
            self.daily_pnl += pnl
            pos['status'] = 'CLOSED_SL'
            pos['exit_price'] = pos['stop_loss']
            pos['pnl'] = pnl
            return {
                'action': 'STOP_LOSS',
                'symbol': symbol,
                'exit_price': pos['stop_loss'],
                'pnl': pnl,
                'pnl_pct': (pnl / (pos['entry_price'] * pos['quantity'])) * 100
            }
        
        # Check take profit
        if current_price >= pos['take_profit']:
            pnl = (current_price - pos['entry_price']) * pos['quantity']
            self.daily_pnl += pnl
            pos['status'] = 'CLOSED_TP'
            pos['exit_price'] = pos['take_profit']
            pos['pnl'] = pnl
            return {
                'action': 'TAKE_PROFIT',
                'symbol': symbol,
                'exit_price': pos['take_profit'],
                'pnl': pnl,
                'pnl_pct': (pnl / (pos['entry_price'] * pos['quantity'])) * 100
            }
        
        return None
    
    def get_status(self):
        """Get current account status"""
        open_count = sum(1 for p in self.open_positions.values() if p['status'] == 'OPEN')
        return {
            'account_balance': self.account_balance,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'open_positions': open_count,
            'max_positions': self.position_limit,
            'risk_per_trade': self.risk_per_trade,
            'max_drawdown': self.max_drawdown
        }

# Export for use in bots
if __name__ == "__main__":
    rm = RiskManager(account_balance=10000, risk_per_trade=1.0)
    print("Risk Manager loaded")
