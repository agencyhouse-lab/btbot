#!/bin/bash
echo "🚀 Starting all systems..."
echo ""
echo "Starting dashboard..."
nohup python3 realtime_dashboard.py > dashboard.log 2>&1 & sleep 2

echo "Starting hourly reporter..."
nohup python3 hourly_telegram_reporter_v2.py > hourly_reporter.log 2>&1 & sleep 2

echo "Starting trading bots..."
nohup python3 ps2tradeb_v6_final.py > ps2tradeb_v6.log 2>&1 & sleep 1
nohup python3 btbot_v6_final.py > btbot_v6.log 2>&1 & sleep 1
nohup python3 etbot_v6_final.py > etbot_v6.log 2>&1 & sleep 1
nohup python3 atbot_v6_final.py > atbot_v6.log 2>&1 & sleep 1

echo ""
bash CHECK_STATUS.sh
