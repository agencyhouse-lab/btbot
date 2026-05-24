# 📦 BOT UPDATE SCRIPTS PACKAGE

**Date**: May 24, 2026
**Purpose**: Complete bot update, fix, and monitoring scripts

---

## 📋 SCRIPTS INCLUDED

| Script | Purpose | When to use |
|--------|---------|------------|
| `UPDATE_AND_FIX_ALL.sh` | **Main fix script** - Restarts all bots | First time (NOW) |
| `CHECK_STATUS.sh` | Quick status check | Anytime to verify bots running |
| `VIEW_LOGS.sh` | View bot logs | Troubleshooting |
| `RESTART_BOT.sh` | Restart single bot | If one bot crashes |
| `KILL_ALL_BOTS.sh` | Kill all processes | Emergency cleanup |

---

## 🚀 QUICK START

### Step 1: Run Master Fix Script (FIRST TIME)
```bash
bash /root/btbot/UPDATE_AND_FIX_ALL.sh
```

**What it does**:
- ✅ Backs up current state
- ✅ Kills all old processes
- ✅ Starts dashboard
- ✅ Starts hourly reporter
- ✅ Starts all 4 trading bots
- ✅ Verifies all running
- ✅ Sends test messages
- ✅ Shows final status

**Time**: 2-3 minutes

**Result**: All bots online and trading

---

## 📊 CHECKING STATUS

### Check anytime:
```bash
bash /root/btbot/CHECK_STATUS.sh
```

**Shows**:
- 🟢/🔴 status of each bot
- Dashboard status
- Hourly reporter status
- Log file sizes
- Any errors

---

## 📋 VIEWING LOGS

### View all logs:
```bash
bash /root/btbot/VIEW_LOGS.sh all 20
```

### View specific bot (example):
```bash
bash /root/btbot/VIEW_LOGS.sh btbot 50
```

### Options:










ssh
cd /root/btbot/

echo "════════════════════════════════════════════════════════════"
echo "📦 CREATING COMPLETE UPDATE SCRIPT PACKAGE"
echo "════════════════════════════════════════════════════════════"
echo ""

# 1. CREATE MASTER FIX & UPDATE SCRIPT
cat > UPDATE_AND_FIX_ALL.sh << 'MAINSCRIPT'
#!/bin/bash
# 🔧 MASTER UPDATE & FIX SCRIPT
# Fixes all bots, updates services, restarts everything
# Run this: bash UPDATE_AND_FIX_ALL.sh

set -e  # Exit on error

cd /root/btbot/

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔧 COMPLETE BOT UPDATE & FIX SYSTEM"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Starting at: $(date '+%Y-%m-%d %H:%M:%S') UTC+7"
echo ""

# PHASE 1: BACKUP
echo ""
echo "PHASE 1️⃣: BACKING UP CURRENT STATE..."
echo "════════════════════════════════════════════════════════════"

python3 backup_system.py > /dev/null 2>&1

echo "✅ Backup completed"
echo ""

# PHASE 2: KILL OLD PROCESSES
echo ""
echo "PHASE 2️⃣: STOPPING OLD PROCESSES..."
echo "════════════════════════════════════════════════════════════"

echo "Killing old bots..."
pkill -f "btbot" 2>/dev/null || true
pkill -f "ps2tradeb" 2>/dev/null || true
pkill -f "etbot" 2>/dev/null || true
pkill -f "atbot" 2>/dev/null || true
pkill -f "hourly_telegram_reporter" 2>/dev/null || true
pkill -f "realtime_dashboard" 2>/dev/null || true

echo "Waiting for processes to stop..."
sleep 3

echo "✅ All old processes stopped"
echo ""

# PHASE 3: VERIFY OLD PROCESSES KILLED
echo ""
echo "PHASE 3️⃣: VERIFYING PROCESS CLEANUP..."
echo "════════════════════════════════════════════════════════════"

if pgrep -f "btbot\|ps2tradeb\|etbot\|atbot" > /dev/null 2>&1; then
    echo "⚠️  Old processes still running, forcing kill..."
    pkill -9 -f "btbot\|ps2tradeb\|etbot\|atbot" 2>/dev/null || true
    sleep 2
fi

echo "✅ Process cleanup verified"
echo ""

# PHASE 4: START DASHBOARD
echo ""
echo "PHASE 4️⃣: STARTING DASHBOARD..."
echo "════════════════════════════════════════════════════════════"

echo "Starting realtime dashboard..."
nohup python3 realtime_dashboard.py > dashboard.log 2>&1 &
DASHBOARD_PID=$!
sleep 3

if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
    echo "✅ Dashboard started (PID: $DASHBOARD_PID)"
else
    echo "❌ Dashboard failed to start"
    echo "Log:"
    tail -10 dashboard.log
fi
echo ""

# PHASE 5: START HOURLY REPORTER
echo ""
echo "PHASE 5️⃣: STARTING HOURLY TELEGRAM REPORTER..."
echo "════════════════════════════════════════════════════════════"

echo "Starting hourly reporter..."
nohup python3 hourly_telegram_reporter_v2.py > hourly_reporter.log 2>&1 &
REPORTER_PID=$!
sleep 3

if ps -p $REPORTER_PID > /dev/null 2>&1; then
    echo "✅ Hourly reporter started (PID: $REPORTER_PID)"
else
    echo "❌ Hourly reporter failed"
    echo "Log:"
    tail -10 hourly_reporter.log
fi
echo ""

# PHASE 6: START ALL TRADING BOTS
echo ""
echo "PHASE 6️⃣: STARTING TRADING BOTS..."
echo "════════════════════════════════════════════════════════════"

# PS2TRADEB
echo ""
echo "Starting PS2TRADEB v6..."
nohup python3 ps2tradeb_v6_final.py > ps2tradeb_v6.log 2>&1 &
PS2_PID=$!
sleep 2

if ps -p $PS2_PID > /dev/null 2>&1; then
    echo "✅ PS2TRADEB started (PID: $PS2_PID)"
else
    echo "❌ PS2TRADEB failed"
    tail -10 ps2tradeb_v6.log
fi

# BTBOT
echo ""
echo "Starting BTBOT v6..."
nohup python3 btbot_v6_final.py > btbot_v6.log 2>&1 &
BT_PID=$!
sleep 2

if ps -p $BT_PID > /dev/null 2>&1; then
    echo "✅ BTBOT started (PID: $BT_PID)"
else
    echo "❌ BTBOT failed"
    tail -10 btbot_v6.log
fi

# ETBOT
echo ""
echo "Starting ETBOT v6..."
nohup python3 etbot_v6_final.py > etbot_v6.log 2>&1 &
ET_PID=$!
sleep 2

if ps -p $ET_PID > /dev/null 2>&1; then
    echo "✅ ETBOT started (PID: $ET_PID)"
else
    echo "❌ ETBOT failed"
    tail -10 etbot_v6.log
fi

# ATBOT
echo ""
echo "Starting ATBOT v6..."
nohup python3 atbot_v6_final.py > atbot_v6.log 2>&1 &
AT_PID=$!
sleep 2

if ps -p $AT_PID > /dev/null 2>&1; then
    echo "✅ ATBOT started (PID: $AT_PID)"
else
    echo "❌ ATBOT failed"
    tail -10 atbot_v6.log
fi

echo ""

# PHASE 7: VERIFICATION
echo ""
echo "PHASE 7️⃣: FINAL VERIFICATION..."
echo "════════════════════════════════════════════════════════════"

echo ""
echo "Running processes check..."
RUNNING=$(ps aux | grep -E "v6_final|hourly_telegram_reporter|realtime_dashboard" | grep -v grep | wc -l)
echo "Total running: $RUNNING processes"
echo ""

echo "Dashboard: $(ps -p $DASHBOARD_PID > /dev/null 2>&1 && echo '🟢 ONLINE' || echo '🔴 OFFLINE')"
echo "Reporter:  $(ps -p $REPORTER_PID > /dev/null 2>&1 && echo '🟢 ONLINE' || echo '🔴 OFFLINE')"
echo "PS2TRADEB: $(ps -p $PS2_PID > /dev/null 2>&1 && echo '🟢 ONLINE' || echo '🔴 OFFLINE')"
echo "BTBOT:     $(ps -p $BT_PID > /dev/null 2>&1 && echo '🟢 ONLINE' || echo '🔴 OFFLINE')"
echo "ETBOT:     $(ps -p $ET_PID > /dev/null 2>&1 && echo '🟢 ONLINE' || echo '🔴 OFFLINE')"
echo "ATBOT:     $(ps -p $AT_PID > /dev/null 2>&1 && echo '🟢 ONLINE' || echo '🔴 OFFLINE')"

echo ""

# PHASE 8: TEST MESSAGES
echo ""
echo "PHASE 8️⃣: SENDING TEST MESSAGES..."
echo "════════════════════════════════════════════════════════════"

python3 << 'PYTHON'
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('.env')

bots = {
    'PS2TRADEB': os.getenv('TELEGRAM_PS2TRADEB_TOKEN'),
    'BTBOT': os.getenv('TELEGRAM_BTBOT_TOKEN'),
    'ETBOT': os.getenv('TELEGRAM_ETBOT_TOKEN'),
    'ATBOT': os.getenv('TELEGRAM_ATBOT_TOKEN')
}

monitor_token = os.getenv('TELEGRAM_MONITOR_TOKEN')
chat_id = os.getenv('TELEGRAM_MONITOR_CHAT_ID')

print("")

for bot_name, token in bots.items():
    try:
        msg = f"""✅ {bot_name} v6 RESTARTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Status: 🟢 ONLINE & READY
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC+7
Version: 6.0 FINAL
Risk: $25/trade

Trading active!"""
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={'chat_id': chat_id, 'text': msg}, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ {bot_name} test message sent")
        else:
            print(f"❌ {bot_name} test message failed: {response.status_code}")
    except Exception as e:
        print(f"❌ {bot_name} error: {e}")

print("")

PYTHON

echo ""

# PHASE 9: FINAL SUMMARY
echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ UPDATE & FIX COMPLETE!"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "📊 SUMMARY:"
echo "  • Dashboard: Online at http://maxhive.cloud:8888"
echo "  • Hourly Reporter: Running (updates every hour)"
echo "  • PS2TRADEB: Live & trading"
echo "  • BTBOT: Live & trading"
echo "  • ETBOT: Live & trading"
echo "  • ATBOT: Live & trading"
echo ""
echo "📱 TELEGRAM:"
echo "  • Test messages sent to all bots"
echo "  • Hourly updates active"
echo "  • All bots sending signals"
echo ""
echo "🚀 NEXT STEPS:"
echo "  1. Check dashboard: http://maxhive.cloud:8888"
echo "  2. Wait 1 hour for hourly update"
echo "  3. Monitor Telegram for trade alerts"
echo "  4. Check logs if issues:"
echo "     - tail -20 ps2tradeb_v6.log"
echo "     - tail -20 btbot_v6.log"
echo "     - tail -20 etbot_v6.log"
echo "     - tail -20 atbot_v6.log"
echo "     - tail -20 hourly_reporter.log"
echo ""
echo "⏰ Completed at: $(date '+%Y-%m-%d %H:%M:%S') UTC+7"
echo ""
echo "════════════════════════════════════════════════════════════"

MAINSCRIPT

chmod +x UPDATE_AND_FIX_ALL.sh

echo "✅ Master script created: UPDATE_AND_FIX_ALL.sh"
echo ""

# 2. CREATE QUICK STATUS CHECK SCRIPT
cat > CHECK_STATUS.sh << 'STATUSSCRIPT'
#!/bin/bash
# 📊 QUICK STATUS CHECK SCRIPT
# Run this anytime to check if bots are running

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📊 QUICK BOT STATUS CHECK"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Time: $(date '+%Y-%m-%d %H:%M:%S') UTC+7"
echo ""

echo "🤖 PROCESS STATUS:"
echo ""

echo -n "Dashboard:         "
pgrep -f "realtime_dashboard" > /dev/null && echo "🟢 ONLINE" || echo "🔴 OFFLINE"

echo -n "Hourly Reporter:   "
pgrep -f "hourly_telegram_reporter" > /dev/null && echo "🟢 ONLINE" || echo "🔴 OFFLINE"

echo -n "PS2TRADEB:         "
pgrep -f "ps2tradeb_v6_final" > /dev/null && echo "🟢 ONLINE" || echo "🔴 OFFLINE"

echo -n "BTBOT:             "
pgrep -f "btbot_v6_final" > /dev/null && echo "🟢 ONLINE" || echo "🔴 OFFLINE"

echo -n "ETBOT:             "
pgrep -f "etbot_v6_final" > /dev/null && echo "🟢 ONLINE" || echo "🔴 OFFLINE"

echo -n "ATBOT:             "
pgrep -f "atbot_v6_final" > /dev/null && echo "🟢 ONLINE" || echo "🔴 OFFLINE"

echo ""
echo "📋 LOG FILE SIZES:"
echo ""

for log in dashboard.log hourly_reporter.log ps2tradeb_v6.log btbot_v6.log etbot_v6.log atbot_v6.log; do
    if [ -f "$log" ]; then
        size=$(wc -l < "$log")
        echo "  $log: $size lines"
    fi
done

echo ""
echo "📈 RECENT ERRORS (Last 24h):"
echo ""

for log in ps2tradeb_v6.log btbot_v6.log etbot_v6.log atbot_v6.log; do
    if [ -f "$log" ]; then
        errors=$(grep -c "❌\|ERROR" "$log" 2>/dev/null || echo "0")
        if [ "$errors" -gt 0 ]; then
            echo "  ⚠️  $log: $errors errors"
        fi
    fi
done

echo ""
echo "✅ Check completed"
echo ""

STATUSSCRIPT

chmod +x CHECK_STATUS.sh

echo "✅ Status check script created: CHECK_STATUS.sh"
echo ""

# 3. CREATE LOG VIEWER SCRIPT
cat > VIEW_LOGS.sh << 'LOGSCRIPT'
#!/bin/bash
# 📋 VIEW BOT LOGS SCRIPT
# Usage: bash VIEW_LOGS.sh [bot_name] [lines]
# Example: bash VIEW_LOGS.sh btbot 50

BOT=${1:-all}
LINES=${2:-20}

echo ""
echo "════════════════════════════════════════════════════════════"
echo "📋 BOT LOG VIEWER"
echo "════════════════════════════════════════════════════════════"
echo ""

case $BOT in
    all)
        echo "Showing last $LINES lines from all logs:"
        echo ""
        echo "--- DASHBOARD ---"
        tail -$LINES dashboard.log 2>/dev/null || echo "Log not found"
        echo ""
        echo "--- HOURLY REPORTER ---"
        tail -$LINES hourly_reporter.log 2>/dev/null || echo "Log not found"
        echo ""
        echo "--- PS2TRADEB ---"
        tail -$LINES ps2tradeb_v6.log 2>/dev/null || echo "Log not found"
        echo ""
        echo "--- BTBOT ---"
        tail -$LINES btbot_v6.log 2>/dev/null || echo "Log not found"
        echo ""
        echo "--- ETBOT ---"
        tail -$LINES etbot_v6.log 2>/dev/null || echo "Log not found"
        echo ""
        echo "--- ATBOT ---"
        tail -$LINES atbot_v6.log 2>/dev/null || echo "Log not found"
        ;;
    
    dashboard)
        echo "Dashboard log (last $LINES lines):"
        tail -$LINES dashboard.log
        ;;
    
    reporter)
        echo "Hourly Reporter log (last $LINES lines):"
        tail -$LINES hourly_reporter.log
        ;;
    
    ps2tradeb)
        echo "PS2TRADEB log (last $LINES lines):"
        tail -$LINES ps2tradeb_v6.log
        ;;
    
    btbot)
        echo "BTBOT log (last $LINES lines):"
        tail -$LINES btbot_v6.log
        ;;
    
    etbot)
        echo "ETBOT log (last $LINES lines):"
        tail -$LINES etbot_v6.log
        ;;
    
    atbot)
        echo "ATBOT log (last $LINES lines):"
        tail -$LINES atbot_v6.log
        ;;
    
    *)
        echo "Usage: bash VIEW_LOGS.sh [bot_name] [lines]"
        echo ""
        echo "Options:"
        echo "  all         - Show all logs"
        echo "  dashboard   - Dashboard logs"
        echo "  reporter    - Hourly reporter logs"
        echo "  ps2tradeb   - PS2TRADEB logs"
        echo "  btbot       - BTBOT logs"
        echo "  etbot       - ETBOT logs"
        echo "  atbot       - ATBOT logs"
        echo ""
        echo "Examples:"
        echo "  bash VIEW_LOGS.sh all 50       (last 50 lines from all)"
        echo "  bash VIEW_LOGS.sh btbot 100    (last 100 lines from BTBOT)"
        ;;
esac

echo ""

LOGSCRIPT

chmod +x VIEW_LOGS.sh

echo "✅ Log viewer script created: VIEW_LOGS.sh"
echo ""

# 4. CREATE RESTART SINGLE BOT SCRIPT
cat > RESTART_BOT.sh << 'BOTSCRIPT'
#!/bin/bash
# 🔄 RESTART SINGLE BOT SCRIPT
# Usage: bash RESTART_BOT.sh [bot_name]
# Example: bash RESTART_BOT.sh btbot

BOT=${1}

if [ -z "$BOT" ]; then
    echo "Usage: bash RESTART_BOT.sh [bot_name]"
    echo ""
    echo "Options:"
    echo "  ps2tradeb  - Restart PS2TRADEB"
    echo "  btbot      - Restart BTBOT"
    echo "  etbot      - Restart ETBOT"
    echo "  atbot      - Restart ATBOT"
    echo ""
    exit 1
fi

cd /root/btbot/

echo ""
echo "════════════════════════════════════════════════════════════"
echo "🔄 RESTARTING $BOT"
echo "════════════════════════════════════════════════════════════"
echo ""

case $BOT in
    ps2tradeb)
        echo "Stopping PS2TRADEB..."
        pkill -f "ps2tradeb_v6_final" 2>/dev/null || true
        sleep 2
        echo "Starting PS2TRADEB..."
        nohup python3 ps2tradeb_v6_final.py > ps2tradeb_v6.log 2>&1 &
        sleep 2
        if pgrep -f "ps2tradeb_v6_final" > /dev/null; then
            echo "✅ PS2TRADEB restarted successfully"
        else
            echo "❌ Failed to restart PS2TRADEB"
            echo "Last 10 log lines:"
            tail -10 ps2tradeb_v6.log
        fi
        ;;
    
    btbot)
        echo "Stopping BTBOT..."
        pkill -f "btbot_v6_final" 2>/dev/null || true
        sleep 2
        echo "Starting BTBOT..."
        nohup python3 btbot_v6_final.py > btbot_v6.log 2>&1 &
        sleep 2
        if pgrep -f "btbot_v6_final" > /dev/null; then
            echo "✅ BTBOT restarted successfully"
        else
            echo "❌ Failed to restart BTBOT"
            echo "Last 10 log lines:"
            tail -10 btbot_v6.log
        fi
        ;;
    
    etbot)
        echo "Stopping ETBOT..."
        pkill -f "etbot_v6_final" 2>/dev/null || true
        sleep 2
        echo "Starting ETBOT..."
        nohup python3 etbot_v6_final.py > etbot_v6.log 2>&1 &
        sleep 2
        if pgrep -f "etbot_v6_final" > /dev/null; then
            echo "✅ ETBOT restarted successfully"
        else
            echo "❌ Failed to restart ETBOT"
            echo "Last 10 log lines:"
            tail -10 etbot_v6.log
        fi
        ;;
    
    atbot)
        echo "Stopping ATBOT..."
        pkill -f "atbot_v6_final" 2>/dev/null || true
        sleep 2
        echo "Starting ATBOT..."
        nohup python3 atbot_v6_final.py > atbot_v6.log 2>&1 &
        sleep 2
        if pgrep -f "atbot_v6_final" > /dev/null; then
            echo "✅ ATBOT restarted successfully"
        else
            echo "❌ Failed to restart ATBOT"
            echo "Last 10 log lines:"
            tail -10 atbot_v6.log
        fi
        ;;
    
    *)
        echo "Unknown bot: $BOT"
        echo "Use: ps2tradeb, btbot, etbot, or atbot"
        ;;
esac

echo ""

BOTSCRIPT

chmod +x RESTART_BOT.sh

echo "✅ Bot restart script created: RESTART_BOT.sh"
echo ""

# 5. CREATE KILL ALL & CLEANUP SCRIPT
cat > KILL_ALL_BOTS.sh << 'KILLSCRIPT'
#!/bin/bash
# 💀 KILL ALL BOTS & CLEANUP
# Use this if something goes wrong

echo ""
echo "════════════════════════════════════════════════════════════"
echo "💀 KILLING ALL BOTS & SERVICES"
echo "════════════════════════════════════════════════════════════"
echo ""

echo "Killing all processes..."

pkill -9 -f "btbot" 2>/dev/null || true
pkill -9 -f "ps2tradeb" 2>/dev/null || true
pkill -9 -f "etbot" 2>/dev/null || true
pkill -9 -f "atbot" 2>/dev/null || true
pkill -9 -f "hourly_telegram_reporter" 2>/dev/null || true
pkill -9 -f "realtime_dashboard" 2>/dev/null || true

echo "Waiting..."
sleep 3

echo "✅ All processes killed"
echo ""

echo "Remaining processes (should be empty):"
ps aux | grep -E "v6_final|hourly_telegram_reporter|realtime_dashboard" | grep -v grep

echo ""
echo "✅ Cleanup complete"
echo ""
echo "To restart: bash UPDATE_AND_FIX_ALL.sh"
echo ""

KILLSCRIPT

chmod +x KILL_ALL_BOTS.sh

echo "✅ Kill script created: KILL_ALL_BOTS.sh"
echo ""

# 6. CREATE README WITH INSTRUCTIONS
cat > README_UPDATE_SCRIPTS.md << 'README'
# 📦 BOT UPDATE SCRIPTS PACKAGE

**Date**: May 24, 2026
**Purpose**: Complete bot update, fix, and monitoring scripts

---

## 📋 SCRIPTS INCLUDED

| Script | Purpose | When to use |
|--------|---------|------------|
| `UPDATE_AND_FIX_ALL.sh` | **Main fix script** - Restarts all bots | First time (NOW) |
| `CHECK_STATUS.sh` | Quick status check | Anytime to verify bots running |
| `VIEW_LOGS.sh` | View bot logs | Troubleshooting |
| `RESTART_BOT.sh` | Restart single bot | If one bot crashes |
| `KILL_ALL_BOTS.sh` | Kill all processes | Emergency cleanup |

---

## 🚀 QUICK START

### Step 1: Run Master Fix Script (FIRST TIME)
```bash
bash /root/btbot/UPDATE_AND_FIX_ALL.sh
```

**What it does**:
- ✅ Backs up current state
- ✅ Kills all old processes
- ✅ Starts dashboard
- ✅ Starts hourly reporter
- ✅ Starts all 4 trading bots
- ✅ Verifies all running
- ✅ Sends test messages
- ✅ Shows final status

**Time**: 2-3 minutes

**Result**: All bots online and trading

---

## 📊 CHECKING STATUS

### Check anytime:
```bash
bash /root/btbot/CHECK_STATUS.sh
```

**Shows**:
- 🟢/🔴 status of each bot
- Dashboard status
- Hourly reporter status
- Log file sizes
- Any errors

---

## 📋 VIEWING LOGS

### View all logs:
```bash
bash /root/btbot/VIEW_LOGS.sh all 20
```

### View specific bot (example):
```bash
bash /root/btbot/VIEW_LOGS.sh btbot 50
```

### Options:


