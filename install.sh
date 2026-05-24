#!/bin/bash
# install.sh — ps1trade PAPER bot installer
# Run: cd /root/ps1trade && bash install.sh
set -e
DIR="/root/ps1trade"
NAME="ps1trade"
echo "════════════════════════════════════════"
echo "  📄 $NAME PAPER Bot — Installer"
echo "════════════════════════════════════════"

# 1. Packages
echo -e "\n📦 Installing packages..."
pip3 install python-binance requests pandas numpy ta python-dotenv \
    --break-system-packages -q
echo "   ✅ Done"

# 2. Dirs
mkdir -p "$DIR/logs"

# 3. Binance test (read-only)
echo -e "\n🔗 Testing Binance (read-only)..."
python3 - << 'EOF'
import os, sys
sys.path.insert(0, '/root/ps1trade')
from dotenv import load_dotenv
load_dotenv('/root/ps1trade/.env', override=True)
from binance.client import Client
c = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_SECRET_KEY"), testnet=True)
tick = c.get_symbol_ticker(symbol="BTCUSDT")
print(f"   ✅ Binance OK (read-only)")
print(f"   ✅ BTC price: ${float(tick['price']):,.2f}")
EOF

# 4. Telegram test
echo -e "\n📲 Testing Telegram..."
python3 - << 'EOF'
import requests, os
from dotenv import load_dotenv
load_dotenv('/root/ps1trade/.env', override=True)
tok = os.getenv("TELEGRAM_TOKEN"); chat = os.getenv("TELEGRAM_CHAT_ID")
r = requests.get(f"https://api.telegram.org/bot{tok}/getMe", timeout=10)
print(f"   ✅ Bot: @{r.json()['result']['username']}")
requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json={
    "chat_id": chat, "parse_mode": "Markdown",
    "text": "📄[PS1TRADE-PAPER] ✅ *Installation Complete!*\nPaper trading bot ready\n💰 Virtual balance: $10,000\n_No real orders will be placed_ 🧪"
})
print(f"   ✅ Telegram message sent!")
EOF

# 5. Systemd service
echo -e "\n⚙️  Installing systemd service..."
cat > /etc/systemd/system/ps1trade.service << SVCEOF
[Unit]
Description=ps1trade v2.1 - Binance Paper Trading Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/ps1trade
ExecStart=/usr/bin/python3 /root/ps1trade/main.py
Restart=on-failure
RestartSec=30
Environment=PYTHONUNBUFFERED=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SVCEOF

systemctl daemon-reload
systemctl enable ps1trade
systemctl stop ps1trade 2>/dev/null || true
sleep 1
systemctl start ps1trade
echo "   ✅ ps1trade service started"
sleep 3

echo -e "\n🔍 Status:"
systemctl status ps1trade --no-pager -l | head -20
echo -e "\n📋 Logs:"
journalctl -u ps1trade -n 15 --no-pager

echo -e "\n════════════════════════════════════════"
echo "  ✅ ps1trade PAPER is running!"
echo "  Watch: journalctl -u ps1trade -f"
echo "  Stop:  systemctl stop ps1trade"
echo "════════════════════════════════════════"
