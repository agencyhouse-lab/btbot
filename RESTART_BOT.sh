#!/bin/bash
BOT=${1}
if [ -z "$BOT" ]; then 
  echo "Usage: bash RESTART_BOT.sh [ps2tradeb|btbot|etbot|atbot]"
  exit 1
fi
echo "🔄 Restarting $BOT..."
pkill -f "${BOT}_v6" 2>/dev/null || true
sleep 2
nohup python3 ${BOT}_v6_final.py > ${BOT}_v6.log 2>&1 &
sleep 2
pgrep -f "${BOT}_v6" > /dev/null && echo "✅ $BOT started" || (echo "❌ Failed"; tail -5 ${BOT}_v6.log)
