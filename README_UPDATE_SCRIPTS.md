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
