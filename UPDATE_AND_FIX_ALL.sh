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



