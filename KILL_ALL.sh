#!/bin/bash
echo "💀 Killing all bots..."
pkill -9 -f "btbot\|ps2tradeb\|etbot\|atbot\|hourly\|realtime" 2>/dev/null || true
sleep 2
echo "✅ All killed"
