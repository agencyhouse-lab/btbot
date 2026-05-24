#!/bin/bash
cd /root/btbot/
git add *.log *.json BOT_STATUS.md 2>/dev/null || true
git commit -m "Logs: $(date)" 2>/dev/null || true
git push origin main 2>/dev/null || true
