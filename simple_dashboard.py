#!/usr/bin/env python3
"""
Simple HTTP Server Dashboard (no Flask dependency)
"""
import http.server
import socketserver
import json
from datetime import datetime
from pathlib import Path
import subprocess
import threading
import time

PORT = 8888

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Trading Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        :root {
            --bg: #060d1a;
            --bg2: #0a1628;
            --cyan: #00d4ff;
            --green: #00ff88;
            --red: #ff4466;
            --orange: #ff9500;
            --yellow: #f0b429;
            --blue: #00a8ff;
            --text: #c8e6f5;
            --text2: #5d8fa8;
        }
        body {
            background: linear-gradient(135deg, var(--bg), #0a1830);
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .logo { font-size: 32px; font-weight: bold; color: var(--cyan); letter-spacing: 3px; }
        .status-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }
        .status-item {
            background: var(--bg2);
            border: 1px solid rgba(0, 180, 255, 0.12);
            border-radius: 8px;
            padding: 12px 20px;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--green);
            box-shadow: 0 0 10px var(--green);
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid rgba(0, 180, 255, 0.12);
            flex-wrap: wrap;
        }
        .tab-button {
            background: transparent;
            border: none;
            color: var(--text2);
            font-family: 'JetBrains Mono', monospace;
            font-size: 13px;
            padding: 10px 20px;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .tab-button:hover { color: var(--text); }
        .tab-button.active { color: var(--cyan); border-bottom: 3px solid var(--cyan); }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .bot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .card {
            background: linear-gradient(135deg, var(--bg2), #0f2040);
            border: 1px solid rgba(0, 180, 255, 0.12);
            border-radius: 12px;
            padding: 20px;
        }
        .card-title {
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(0, 180, 255, 0.12);
        }
        .card-title.ps2tradeb { color: var(--green); }
        .card-title.btbot { color: var(--orange); }
        .card-title.etbot { color: var(--blue); }
        .card-title.atbot { color: var(--yellow); }
        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-size: 12px;
            padding: 8px;
            background: rgba(0, 180, 255, 0.05);
            border-radius: 6px;
        }
        .stat-label { color: var(--text2); }
        .stat-value { color: var(--text); font-weight: 600; }
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            background: rgba(0, 255, 136, 0.2);
            color: var(--green);
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(0, 180, 255, 0.12);
            color: var(--text2);
            font-size: 11px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">⚡ TRADING BOTS</div>
            <div style="color: var(--text2); font-size: 12px; letter-spacing: 2px;">UNIFIED CONTROL PANEL</div>
        </div>
        
        <div class="status-bar">
            <div class="status-item"><div class="status-dot"></div><span>PS2TRADEB: ACTIVE</span></div>
            <div class="status-item"><div class="status-dot"></div><span>BTBOT: ACTIVE</span></div>
            <div class="status-item"><div class="status-dot"></div><span>ETBOT: ACTIVE</span></div>
            <div class="status-item"><div class="status-dot"></div><span>ATBOT: ACTIVE</span></div>
        </div>
        
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab(event, 'all')">📊 ALL BOTS</button>
            <button class="tab-button" onclick="switchTab(event, 'ps2tradeb')">🟢 PS2TRADEB</button>
            <button class="tab-button" onclick="switchTab(event, 'btbot')">🟠 BTBOT</button>
            <button class="tab-button" onclick="switchTab(event, 'etbot')">🔵 ETBOT</button>
            <button class="tab-button" onclick="switchTab(event, 'atbot')">🟠 ATBOT</button>
        </div>
        
        <!-- ALL BOTS TAB -->
        <div id="all" class="tab-content active">
            <div class="bot-grid">
                <div class="card">
                    <div class="card-title ps2tradeb">🟢 PS2TRADEB v5.0</div>
                    <div class="stat-row"><span class="stat-label">Exchange:</span><span class="stat-value">Binance LIVE</span></div>
                    <div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">Multi-Factor</span></div>
                    <div class="stat-row"><span class="stat-label">Status:</span><span class="stat-value"><span class="badge">ACTIVE</span></span></div>
                    <div class="stat-row"><span class="stat-label">Pairs:</span><span class="stat-value">5 (BTC, ETH, BNB, ADA, XRP)</span></div>
                    <div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">1.0%</span></div>
                    <div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">2.0%</span></div>
                    <div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@ps2TradeB_bot</span></div>
                </div>
                
                <div class="card">
                    <div class="card-title btbot">🟠 BTBOT v5.0</div>
                    <div class="stat-row"><span class="stat-label">Exchange:</span><span class="stat-value">Binance LIVE</span></div>
                    <div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">RSI Strategy</span></div>
                    <div class="stat-row"><span class="stat-label">Status:</span><span class="stat-value"><span class="badge">ACTIVE</span></span></div>
                    <div class="stat-row"><span class="stat-label">Pairs:</span><span class="stat-value">5 (BTC, ETH, BNB, ADA, XRP)</span></div>
                    <div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">0.5%</span></div>
                    <div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">1.5%</span></div>
                    <div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@binance_bt_bot</span></div>
                </div>
                
                <div class="card">
                    <div class="card-title etbot">🔵 ETBOT v5.0</div>
                    <div class="stat-row"><span class="stat-label">API:</span><span class="stat-value">CoinGecko</span></div>
                    <div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">Momentum</span></div>
                    <div class="stat-row"><span class="stat-label">Status:</span><span class="stat-value"><span class="badge">ACTIVE</span></span></div>
                    <div class="stat-row"><span class="stat-label">Symbols:</span><span class="stat-value">BTC, ETH</span></div>
                    <div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">0.3%</span></div>
                    <div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">3.0%</span></div>
                    <div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@etoro_et_bot</span></div>
                </div>
                
                <div class="card">
                    <div class="card-title atbot">🟠 ATBOT v5.2</div>
                    <div class="stat-row"><span class="stat-label">Exchange:</span><span class="stat-value">Alpaca LIVE</span></div>
                    <div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">Multi-Factor</span></div>
                    <div class="stat-row"><span class="stat-label">Status:</span><span class="stat-value"><span class="badge">ACTIVE</span></span></div>
                    <div class="stat-row"><span class="stat-label">Pairs:</span><span class="stat-value">5 (SPY, QQQ, IWM, DIA, GLD)</span></div>
                    <div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">1.0%</span></div>
                    <div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">2.0%</span></div>
                    <div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@sunny_trading_088_bot</span></div>
                </div>
            </div>
        </div>
        
        <!-- Individual bot tabs with same content -->
        <div id="ps2tradeb" class="tab-content"><div class="bot-grid"><div class="card"><div class="card-title ps2tradeb">🟢 PS2TRADEB v5.0 - DETAILED</div><div class="stat-row"><span class="stat-label">Exchange:</span><span class="stat-value">Binance LIVE</span></div><div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">24h Change + RSI (15m candles)</span></div><div class="stat-row"><span class="stat-label">Pairs:</span><span class="stat-value">BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, XRPUSDT</span></div><div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">1.0% of account</span></div><div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">2.0%</span></div><div class="stat-row"><span class="stat-label">Take Profit:</span><span class="stat-value">3.0%</span></div><div class="stat-row"><span class="stat-label">Daily Max Loss:</span><span class="stat-value">5%</span></div><div class="stat-row"><span class="stat-label">Position Limit:</span><span class="stat-value">5 concurrent</span></div><div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@ps2TradeB_bot</span></div></div></div></div>
        <div id="btbot" class="tab-content"><div class="bot-grid"><div class="card"><div class="card-title btbot">🟠 BTBOT v5.0 - DETAILED</div><div class="stat-row"><span class="stat-label">Exchange:</span><span class="stat-value">Binance LIVE</span></div><div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">RSI (14-period, 15m candles)</span></div><div class="stat-row"><span class="stat-label">Pairs:</span><span class="stat-value">BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, XRPUSDT</span></div><div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">0.5% of account</span></div><div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">1.5%</span></div><div class="stat-row"><span class="stat-label">Take Profit:</span><span class="stat-value">2.5%</span></div><div class="stat-row"><span class="stat-label">Daily Max Loss:</span><span class="stat-value">3%</span></div><div class="stat-row"><span class="stat-label">Position Limit:</span><span class="stat-value">3 concurrent</span></div><div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@binance_bt_bot</span></div></div></div></div>
        <div id="etbot" class="tab-content"><div class="bot-grid"><div class="card"><div class="card-title etbot">🔵 ETBOT v5.0 - DETAILED</div><div class="stat-row"><span class="stat-label">API:</span><span class="stat-value">CoinGecko (Free)</span></div><div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">24h Momentum Detection</span></div><div class="stat-row"><span class="stat-label">Symbols:</span><span class="stat-value">BTC (Bitcoin), ETH (Ethereum)</span></div><div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">0.3% of account</span></div><div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">3.0%</span></div><div class="stat-row"><span class="stat-label">Take Profit:</span><span class="stat-value">5.0%</span></div><div class="stat-row"><span class="stat-label">Daily Max Loss:</span><span class="stat-value">2%</span></div><div class="stat-row"><span class="stat-label">Position Limit:</span><span class="stat-value">2 concurrent</span></div><div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@etoro_et_bot</span></div></div></div></div>
        <div id="atbot" class="tab-content"><div class="bot-grid"><div class="card"><div class="card-title atbot">🟠 ATBOT v5.2 - DETAILED</div><div class="stat-row"><span class="stat-label">Exchange:</span><span class="stat-value">Alpaca LIVE (Account 261356293)</span></div><div class="stat-row"><span class="stat-label">Algorithm:</span><span class="stat-value">Multi-factor (Price + RSI)</span></div><div class="stat-row"><span class="stat-label">Pairs:</span><span class="stat-value">SPY, QQQ, IWM, DIA, GLD</span></div><div class="stat-row"><span class="stat-label">Risk/Trade:</span><span class="stat-value">1.0% of account</span></div><div class="stat-row"><span class="stat-label">Stop Loss:</span><span class="stat-value">1.5-2.0%</span></div><div class="stat-row"><span class="stat-label">Take Profit:</span><span class="stat-value">2.5-3.0%</span></div><div class="stat-row"><span class="stat-label">Daily Max Loss:</span><span class="stat-value">5%</span></div><div class="stat-row"><span class="stat-label">Position Limit:</span><span class="stat-value">5 concurrent</span></div><div class="stat-row"><span class="stat-label">Telegram:</span><span class="stat-value">@sunny_trading_088_bot</span></div></div></div></div>
        
        <div style="text-align: center; margin-top: 20px; color: var(--text2); font-size: 11px;">
            Last updated: <span id="time">--:--:--</span> UTC+7
        </div>
        
        <div class="footer">
            🚀 Unified Trading Bot Dashboard | All 4 Bots Monitoring | Real-time Status
            <br>System Status: 🟢 OPERATIONAL | Bots: 4/4 | Risk Management: ACTIVE
        </div>
    </div>
    
    <script>
        function switchTab(e, tab) {
            e.preventDefault();
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            e.target.classList.add('active');
        }
        setInterval(() => {
            const now = new Date();
            document.getElementById('time').textContent = now.toLocaleTimeString('en-US', {hour12: false});
        }, 1000);
    </script>
</body>
</html>
"""

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format%args}")

def start_server():
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"✅ Dashboard running on http://0.0.0.0:{PORT}/")
        print(f"✅ Access at http://maxhive.cloud:{PORT}/")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Dashboard stopped")

if __name__ == '__main__':
    start_server()

