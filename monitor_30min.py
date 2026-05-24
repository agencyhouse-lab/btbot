#!/usr/bin/env python3
"""
📊 30-MINUTE BOT MONITORING REPORT
Sends to GitHub monitoring bot every 30 minutes
"""
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
import requests
import time
from dotenv import load_dotenv

load_dotenv('.env')

class Monitor30Min:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_MONITOR_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_MONITOR_CHAT_ID')
        self.bots = {
            'ps2tradeb': 'PS2TRADEB (Binance Multi-Factor)',
            'btbot': 'BTBOT (Binance RSI)',
            'etbot': 'ETBOT (Momentum Crypto)',
            'atbot': 'ATBOT (Alpaca Stocks)'
        }
    
    def get_bot_status(self):
        """Get status of all bots"""
        status = {}
        
        for bot_name in self.bots.keys():
            result = subprocess.run(['pgrep', '-f', f'{bot_name}_v6'], capture_output=True)
            is_running = result.returncode == 0
            
            # Count trades
            log_file = f'/root/btbot/{bot_name}_v6.log'
            trades = 0
            if Path(log_file).exists():
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    today = datetime.now().strftime('%Y-%m-%d')
                    exits = [l for l in lines if 'TRADE EXIT' in l and today in l]
                    trades = len(exits)
                except:
                    pass
            
            status[bot_name] = {
                'running': is_running,
                'trades_today': trades,
                'label': self.bots[bot_name]
            }
        
        return status
    
    def build_report(self):
        """Build 30-minute report"""
        status = self.get_bot_status()
        
        msg = f"""📊 30-MIN BOT REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC+7

"""
        
        all_online = all(s['running'] for s in status.values())
        
        msg += "🤖 BOT STATUS:\n"
        for bot_name, data in status.items():
            icon = "🟢" if data['running'] else "🔴"
            msg += f"{icon} {data['label']}\n"
            msg += f"   ├─ Status: {'ONLINE' if data['running'] else 'OFFLINE'}\n"
            msg += f"   └─ Trades Today: {data['trades_today']}\n"
            msg += "\n"
        
        msg += f"""📈 SYSTEM:
├─ Overall: {'✅ ALL ONLINE' if all_online else '⚠️ SOME OFFLINE'}
├─ Dashboard: {'🟢' if subprocess.run(['pgrep', '-f', 'realtime_dashboard'], capture_output=True).returncode == 0 else '🔴'}
└─ Reporter: {'🟢' if subprocess.run(['pgrep', '-f', 'hourly_telegram_reporter'], capture_output=True).returncode == 0 else '🔴'}

🔗 Dashboard: http://maxhive.cloud:8888
📡 Next report: In 30 minutes"""
        
        return msg, all_online
    
    def send_report(self):
        """Send report to Telegram"""
        msg, _ = self.build_report()
        
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            requests.post(url, json={'chat_id': self.chat_id, 'text': msg}, timeout=10)
            return True
        except:
            return False
    
    def run_forever(self):
        """Run monitoring every 30 minutes"""
        print(f"🔄 30-Minute monitoring started: {datetime.now()}")
        
        while True:
            try:
                success = self.send_report()
                if success:
                    print(f"✅ Report sent at {datetime.now()}")
                else:
                    print(f"❌ Report failed at {datetime.now()}")
                
                # Wait 30 minutes
                time.sleep(1800)  # 30 minutes = 1800 seconds
            
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(300)  # Retry in 5 min

if __name__ == '__main__':
    monitor = Monitor30Min()
    monitor.run_forever()

