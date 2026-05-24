#!/usr/bin/env python3
"""
🤖 Telegram Bot Monitor - Daily Status Reports
Monitors: atbot.py, ps2tradeb.py, btbot.py, etbot.py
Sends: Daily reports, alerts, performance tracking
Author: Claude (AI Monitor)
"""

import os
import json
import subprocess
import time
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('/root/btbot/.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/btbot/telegram_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '8953130834:AAEq57og5ncNyqpfAVPXVLdeObrdU8WkeB4')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5587885687')
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Bot tracking
BOTS = {
    'atbot': {
        'file': '/root/btbot/atbot.py',
        'log': '/root/btbot/atbot.log',
        'name': '🟠 ATBOT (Alpaca Live)',
        'type': 'live'
    },
    'ps2tradeb': {
        'file': '/root/btbot/ps2tradeb.py',
        'log': '/root/btbot/ps2tradeb.log',
        'name': '🟡 PS2TRADEB (Binance Paper)',
        'type': 'paper'
    },
    'btbot': {
        'file': '/root/btbot/btbot.py',
        'log': '/root/btbot/btbot.log',
        'name': '🟢 BTBOT',
        'type': 'unknown'
    },
    'etbot': {
        'file': '/root/btbot/etbot.py',
        'log': '/root/btbot/etbot.log',
        'name': '🔵 ETBOT',
        'type': 'unknown'
    }
}

class BotMonitor:
    def __init__(self):
        self.last_report_time = None
        self.error_count = {}
        self.status_cache = {}
        
    def send_telegram(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        try:
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(TELEGRAM_URL, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Telegram sent: {len(message)} chars")
                return True
            else:
                logger.error(f"❌ Telegram failed: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Telegram error: {str(e)}")
            return False
    
    def check_bot_running(self, bot_name):
        """Check if bot process is running"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', f'python3.*{bot_name}'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"❌ Check {bot_name} error: {str(e)}")
            return False
    
    def get_bot_status(self, bot_name):
        """Get detailed bot status"""
        bot_info = BOTS.get(bot_name, {})
        is_running = self.check_bot_running(bot_name)
        
        status = {
            'name': bot_info.get('name', bot_name),
            'running': is_running,
            'status': '✅ RUNNING' if is_running else '❌ STOPPED',
            'type': bot_info.get('type', 'unknown'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Read last log entry
        log_file = bot_info.get('log')
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        status['last_log'] = lines[-1].strip()
                        status['log_lines'] = len(lines)
            except Exception as e:
                logger.error(f"❌ Read log {bot_name}: {str(e)}")
        
        return status
    
    def get_account_info(self, bot_name):
        """Extract account info from bot logs"""
        bot_info = BOTS.get(bot_name, {})
        log_file = bot_info.get('log')
        
        account_info = {
            'equity': 'N/A',
            'trades': 0,
            'errors': 0
        }
        
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    
                    # Extract equity
                    if 'Equity=' in content:
                        parts = content.split('Equity=')[-1].split('|')[0].strip()
                        account_info['equity'] = parts
                    
                    # Count trades
                    account_info['trades'] = content.count('TRADE:')
                    
                    # Count errors
                    account_info['errors'] = content.count('ERROR')
            except Exception as e:
                logger.error(f"❌ Parse {bot_name} log: {str(e)}")
        
        return account_info
    
    def generate_daily_report(self):
        """Generate comprehensive daily report"""
        logger.info("📊 Generating daily report...")
        
        report = "<b>📊 DAILY BOT REPORT</b>\n"
        report += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC+7)\n"
        report += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        all_running = True
        total_trades = 0
        total_errors = 0
        
        # Check each bot
        for bot_name in BOTS.keys():
            status = self.get_bot_status(bot_name)
            account = self.get_account_info(bot_name)
            
            emoji = '🟢' if status['running'] else '🔴'
            report += f"{emoji} <b>{status['name']}</b>\n"
            report += f"   Status: {status['status']}\n"
            
            if status['running']:
                report += f"   💰 Equity: {account['equity']}\n"
                report += f"   📈 Trades: {account['trades']}\n"
                report += f"   ⚠️  Errors: {account['errors']}\n"
                total_trades += account['trades']
                total_errors += account['errors']
            else:
                all_running = False
                if 'last_log' in status:
                    report += f"   📝 Last: {status['last_log'][:80]}...\n"
            
            report += "\n"
        
        # Summary
        report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        report += f"<b>Summary:</b>\n"
        report += f"✅ All Bots: {'✅ RUNNING' if all_running else '⚠️ ISSUES'}\n"
        report += f"📊 Total Trades: {total_trades}\n"
        report += f"⚠️  Total Errors: {total_errors}\n"
        report += f"\n🔗 Monitor: <a href='https://github.com/agencyhouse-lab/btbot'>GitHub Repo</a>\n"
        report += f"📱 Chat ID: {TELEGRAM_CHAT_ID}\n"
        
        return report
    
    def check_for_errors(self):
        """Check logs for new errors and alert"""
        for bot_name in BOTS.keys():
            status = self.get_account_info(bot_name)
            
            prev_errors = self.error_count.get(bot_name, 0)
            current_errors = status['errors']
            
            if current_errors > prev_errors:
                new_errors = current_errors - prev_errors
                alert = f"<b>⚠️ ALERT: {BOTS[bot_name]['name']}</b>\n"
                alert += f"New errors detected: +{new_errors}\n"
                alert += f"Total: {current_errors}\n"
                alert += f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
                
                self.send_telegram(alert)
                logger.warning(f"⚠️ Error alert for {bot_name}")
            
            self.error_count[bot_name] = current_errors
    
    def run_daily_report_cycle(self):
        """Run report once per day"""
        now = datetime.now()
        
        # Check if it's 8 AM (report time)
        if now.hour == 8 and now.minute < 5:
            if self.last_report_time is None or \
               (now - self.last_report_time).days >= 1:
                
                report = self.generate_daily_report()
                self.send_telegram(report)
                self.last_report_time = now
                logger.info("✅ Daily report sent")
    
    def run_continuous_monitoring(self):
        """Run continuous monitoring loop"""
        logger.info("🚀 Bot Monitor Started - Monitoring 4 bots")
        logger.info(f"📱 Telegram Chat: {TELEGRAM_CHAT_ID}")
        logger.info(f"⏰ Daily Report: 8:00 AM UTC+7")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                
                # Every 5 minutes: check for errors
                if cycle % 5 == 0:
                    self.check_for_errors()
                
                # Once per day: send full report
                self.run_daily_report_cycle()
                
                # Log status every 30 minutes
                if cycle % 30 == 0:
                    for bot_name in BOTS.keys():
                        status = self.get_bot_status(bot_name)
                        logger.info(f"{status['name']}: {status['status']}")
                
                # Sleep 1 minute between cycles
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Monitor error: {str(e)}")
                time.sleep(60)


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🤖 TELEGRAM BOT MONITOR")
    print("="*60)
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📱 Chat ID: {TELEGRAM_CHAT_ID}")
    print(f"🔗 Token: {TELEGRAM_TOKEN[:20]}...")
    print("="*60 + "\n")
    
    monitor = BotMonitor()
    
    # Send startup notification
    startup_msg = "🚀 <b>Bot Monitor Started</b>\n"
    startup_msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    startup_msg += "📊 Monitoring 4 trading bots\n"
    startup_msg += "📱 Daily reports at 8:00 AM UTC+7\n"
    monitor.send_telegram(startup_msg)
    
    # Run monitoring
    monitor.run_continuous_monitoring()


if __name__ == '__main__':
    main()
