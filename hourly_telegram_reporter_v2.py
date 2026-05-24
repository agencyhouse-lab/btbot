#!/usr/bin/env python3
"""HOURLY STATUS REPORTER"""
import os
import subprocess
import requests
from datetime import datetime
from dotenv import load_dotenv
import time

load_dotenv('.env')

token = os.getenv('TELEGRAM_MONITOR_TOKEN')
chat_id = os.getenv('TELEGRAM_MONITOR_CHAT_ID')

def get_bot_status():
    """Get status of all bots"""
    bots = ['ps2tradeb', 'btbot', 'etbot', 'atbot']
    status = {}
    for bot in bots:
        result = subprocess.run(['pgrep', '-f', f'{bot}_v6'], capture_output=True)
        status[bot] = result.returncode == 0
    return status

def send_report():
    """Send hourly report"""
    status = get_bot_status()
    
    msg = f"""📊 HOURLY BOT REPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC+7

🤖 BOT STATUS:
{'🟢' if status['ps2tradeb'] else '🔴'} PS2TRADEB
{'🟢' if status['btbot'] else '🔴'} BTBOT  
{'🟢' if status['etbot'] else '🔴'} ETBOT
{'🟢' if status['atbot'] else '🔴'} ATBOT

📈 System: {'✅ ALL ONLINE' if all(status.values()) else '⚠️ SOME OFFLINE'}
"""
    
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                     json={'chat_id': chat_id, 'text': msg}, timeout=5)
    except:
        pass

if __name__ == '__main__':
    while True:
        send_report()
        time.sleep(3600)  # Every hour

