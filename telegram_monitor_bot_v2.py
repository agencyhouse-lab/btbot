#!/usr/bin/env python3
"""
📱 Telegram Bot Monitor v2.0 (Simplified)
Monitors: atbot.py, ps2tradeb.py
Sends: Daily reports, error alerts, status updates
"""

import os
import subprocess
import time
import requests
from datetime import datetime
import logging

# Logging setup
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
TELEGRAM_TOKEN = "8953130834:AAEq57og5ncNyqpfAVPXVLdeObrdU8WkeB4"
TELEGRAM_CHAT_ID = "5587885687"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

BOTS = {
    'atbot': {
        'name': '🟠 ATBOT (Alpaca Live)',
        'log': '/root/btbot/atbot.log',
        'process': 'python3.*atbot.py'
    },
    'ps2tradeb': {
        'name': '🟡 PS2TRADEB (Binance Paper)',
        'log': '/root/btbot/ps2tradeb.log',
        'process': 'python3.*ps2tradeb.py'
    }
}

def send_telegram(message):
    """Send Telegram message"""
    try:
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(TELEGRAM_URL, json=payload, timeout=10)
        if response.status_code == 200:
            logger.info(f"✅ Telegram sent: {len(message)} chars")
            return True
        else:
            logger.error(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Telegram exception: {str(e)}")
        return False

def is_bot_running(bot_name):
    """Check if bot is running"""
    try:
        process = BOTS[bot_name]['process']
        result = subprocess.run(
            ['pgrep', '-f', process],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"❌ Process check error: {str(e)}")
        return False

def get_bot_logs(bot_name, lines=10):
    """Get recent bot logs"""
    try:
        log_file = BOTS[bot_name]['log']
        if os.path.exists(log_file):
            result = subprocess.run(
                ['tail', '-n', str(lines), log_file],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
    except Exception as e:
        logger.error(f"❌ Log read error: {str(e)}")
    return "No logs available"

def extract_account_info(bot_name):
    """Extract account info from logs"""
    try:
        log_file = BOTS[bot_name]['log']
        if not os.path.exists(log_file):
            return None
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        info = {}
        for line in lines[-50:]:  # Check last 50 lines
            if 'Account:' in line or 'Equity=' in line or 'Balance' in line:
                info['account_line'] = line.strip()
            if 'ERROR' in line or 'error' in line:
                info['has_error'] = True
            if 'Trading loop' in line or 'trading loop' in line:
                info['loop_running'] = True
        
        return info
    except Exception as e:
        logger.error(f"❌ Account info error: {str(e)}")
        return None

def generate_status_report():
    """Generate daily status report"""
    logger.info("📊 Generating status report...")
    
    report = "<b>📊 BOT STATUS REPORT</b>\n"
    report += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC+7')}\n"
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    all_running = True
    
    for bot_name, bot_info in BOTS.items():
        is_running = is_bot_running(bot_name)
        status_emoji = "🟢" if is_running else "🔴"
        
        report += f"{status_emoji} <b>{bot_info['name']}</b>\n"
        report += f"   Status: {'✅ RUNNING' if is_running else '❌ STOPPED'}\n"
        
        if is_running:
            account_info = extract_account_info(bot_name)
            if account_info:
                if 'account_line' in account_info:
                    line = account_info['account_line']
                    # Truncate long lines
                    if len(line) > 100:
                        line = line[:100] + "..."
                    report += f"   💰 {line}\n"
                
                if account_info.get('has_error'):
                    report += f"   ⚠️  Errors detected\n"
                else:
                    report += f"   ✅ No errors\n"
        
        report += "\n"
        
        if not is_running:
            all_running = False
    
    # Summary
    report += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    report += f"<b>Summary:</b>\n"
    report += f"{'✅ All Bots Running' if all_running else '⚠️ Some Bots Offline'}\n"
    report += f"\n📂 Logs: <a href='https://github.com/agencyhouse-lab/btbot'>GitHub Repo</a>\n"
    
    return report

def send_startup_notification():
    """Send startup message"""
    msg = "🚀 <b>Bot Monitor Started</b>\n"
    msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC+7')}\n"
    msg += "📊 Monitoring 2 bots\n"
    msg += "📱 Daily reports at 8:00 AM UTC+7\n"
    send_telegram(msg)

def main():
    """Main monitoring loop"""
    print("\n" + "="*60)
    print("📱 TELEGRAM BOT MONITOR v2.0")
    print("="*60)
    print(f"⏰ Start: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📱 Chat ID: {TELEGRAM_CHAT_ID}")
    print("="*60 + "\n")
    
    logger.info("🚀 Bot Monitor Started")
    logger.info(f"📊 Monitoring {len(BOTS)} bots")
    
    # Send startup notification
    send_startup_notification()
    
    last_report_hour = None
    cycle = 0
    
    while True:
        try:
            cycle += 1
            now = datetime.now()
            
            # Send daily report at 8 AM
            if now.hour == 8 and now.minute < 5 and last_report_hour != now.hour:
                logger.info("📊 Sending daily report...")
                report = generate_status_report()
                send_telegram(report)
                last_report_hour = now.hour
            
            # Check for errors every 30 minutes
            if cycle % 30 == 0:
                logger.info("🔍 Checking bot status...")
                for bot_name in BOTS.keys():
                    if not is_bot_running(bot_name):
                        alert = f"⚠️ <b>ALERT: {BOTS[bot_name]['name']} OFFLINE</b>\n"
                        alert += f"⏰ {now.strftime('%H:%M:%S')}\n"
                        alert += f"Action: Check /root/btbot/{bot_name}.log\n"
                        send_telegram(alert)
                        logger.warning(f"⚠️ {bot_name} is offline!")
            
            # Log status every hour
            if cycle % 60 == 0:
                logger.info("📊 Status check:")
                for bot_name in BOTS.keys():
                    running = is_bot_running(bot_name)
                    logger.info(f"   {BOTS[bot_name]['name']}: {'✅ RUNNING' if running else '❌ OFFLINE'}")
            
            # Sleep 1 minute
            time.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped")
            msg = "🛑 <b>Bot Monitor Stopped</b>\n"
            msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC+7')}\n"
            send_telegram(msg)
            break
        
        except Exception as e:
            logger.error(f"❌ Monitor error: {str(e)}")
            time.sleep(60)

if __name__ == '__main__':
    main()
