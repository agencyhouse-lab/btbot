#!/bin/bash
BOT=${1:-all}
LINES=${2:-20}
case $BOT in
  all) echo "=== LAST $LINES LINES FROM ALL ==="; echo ""
    for log in dashboard.log hourly_reporter.log ps2tradeb_v6.log btbot_v6.log etbot_v6.log atbot_v6.log; do
      if [ -f "$log" ]; then
        echo "--- $log ---"; tail -$LINES "$log" 2>/dev/null; echo ""
      fi
    done ;;
  *) 
    if [ -f "${BOT}_v6.log" ]; then
      echo "--- ${BOT}_v6.log ---"; tail -$LINES "${BOT}_v6.log"
    else
      echo "Log not found for: $BOT"
    fi ;;
esac
