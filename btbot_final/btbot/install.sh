#!/bin/bash
# install.sh — btbot LIVE bot installer
# Run: cd /root/btbot && bash install.sh
set -e
DIR="/root/btbot"
NAME="btbot"
echo "════════════════════════════════════════"
echo "  🔴 $NAME LIVE Bot — Installer"
echo "════════════════════════════════════════"

# 1. Packages
echo -e "\n📦 Installing packages..."
pip3 install python-binance requests pandas numpy ta python-dotenv \
    --break-system-packages -q
echo "   ✅ Done"

# 2. Dirs
mkdir -p "$DIR/logs"

# 3. Binance test
echo -e "\n🔗 Testing Binance..."
python3 - << 'EOF'
import os, sys
sys.path.insert(0, '/root/btbot')
from dotenv import load_dotenv
load_dotenv('/root/btbot/.env', override=True)
from binance.client import Client
c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_SECRET_KEY"), testnet=True)
acct = c.get_account()
tick = c.get_symbol_ticker(symbol="BTCUSDT")
bals = [b for b in acct['balances'] if float(b['free']) > 0]
print(f"   ✅ Binance OK | canTrade={acct['canTrade']}")
print(f"   ✅ BTC price: ${float(tick['price']):,.2f}")
[print(f"   💰 {b['asset']:8s}: {float(b['free']):,.6f}") for b in bals]
EOF

# 4. Telegram test
echo -e "\n📲 Testing Telegram..."
python3 - << 'EOF'
import requests, os
from dotenv import load_dotenv
load_dotenv('/root/btbot/.env', override=True)
tok = os.getenv("TELEGRAM_TOKEN"); chat = os.getenv("TELEGRAM_CHAT_ID")
r = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=10)
print(f"   ✅ Bot: @{r.json()['result']['username']}")
requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json={
    "chat_id": chat, "parse_mode": "Markdown",
    "text": "🔴[BTBOT-LIVE] ✅ *Installation Complete!*\nBinance Testnet connected\nStarting LIVE bot now 🚀"
})
print(f"   ✅ Telegram message sent!")
EOF

# 5. Systemd service
echo -e "\n⚙️  Installing systemd service..."
cat > /etc/systemd/system/btbot.service << SVCEOF
[Unit]
Description=btbot v2.1 - Binance Live Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/btbot
ExecStart=/usr/bin/python3 /root/btbot/main.py
Restart=on-failure
RestartSec=30
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable btbot
systemctl stop btbot 2>/dev/null || true
sleep 1
systemctl start btbot
echo "   ✅ btbot service started"
sleep 3

echo -e "\n🔍 Status:"
systemctl status btbot --no-pager -l | head -20
echo -e "\n📋 Logs:"
journalctl -u btbot -n 15 --no-pager

echo -e "\n════════════════════════════════════════"
echo "  ✅ btbot LIVE is running!"
echo "  Watch: journalctl -u btbot -f"
echo "  Stop:  systemctl stop btbot"
echo "════════════════════════════════════════"
