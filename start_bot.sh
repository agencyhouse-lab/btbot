#!/bin/bash

echo "🚀 Starting Bot at $(date)" | tee -a bot_activity.log

# Check which bot to run
if [ "$1" == "atbot" ]; then
    echo "Starting Alpaca Trading Bot..."
    python3 /root/btbot/atbot.py >> bot_activity.log 2>&1 &
elif [ "$1" == "ps1" ]; then
    echo "Starting PS1 Trading Bot..."
    python3 /root/btbot/ps1trade.py >> bot_activity.log 2>&1 &
else
    echo "Usage: ./start_bot.sh [atbot|ps1]"
    exit 1
fi

BOT_PID=$!
echo "Bot started with PID: $BOT_PID" | tee -a bot_activity.log

