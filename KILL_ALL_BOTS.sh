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

