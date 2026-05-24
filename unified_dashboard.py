#!/usr/bin/env python3
"""
🎨 UNIFIED TRADING BOT DASHBOARD
All 4 bots in one interface with tabs
"""
import os
import json
import time
import subprocess
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv

load_dotenv('/root/btbot/.env')

app = Flask(__name__)

# HTML Template with Tabs
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Trading Bot Dashboard | maxhive.cloud</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Syne:wght@600;700;800&display=swap');
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --bg: #060d1a;
            --bg2: #0a1628;
            --bg3: #0f2040;
            --cyan: #00d4ff;
            --green: #00ff88;
            --red: #ff4466;
            --yellow: #f0b429;
            --orange: #ff9500;
            --blue: #00a8ff;
            --text: #c8e6f5;
            --text2: #5d8fa8;
            --border: rgba(0, 180, 255, 0.12);
        }
        
        body {
            background: linear-gradient(135deg, var(--bg) 0%, #0a1830 100%);
            font-family: 'JetBrains Mono', monospace;
            color: var(--text);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .logo {
            font-family: 'Syne', sans-serif;
            font-size: 32px;
            font-weight: 800;
            color: var(--cyan);
            letter-spacing: 3px;
            margin-bottom: 10px;
        }
        
        .status-bar {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .status-item {
            background: var(--bg2);
            border: 1px solid var(--border);
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
            animation: pulse 2s infinite;
        }
        
        .status-dot.active {
            background: var(--green);
            box-shadow: 0 0 10px var(--green);
        }
        
        .status-dot.inactive {
            background: var(--red);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid var(--border);
            padding-bottom: 10px;
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
            border-radius: 8px 8px 0 0;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }
        
        .tab-button:hover {
            color: var(--text);
            background: var(--bg3);
        }
        
        .tab-button.active {
            color: var(--cyan);
            background: var(--bg3);
            border-bottom: 3px solid var(--cyan);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .bot-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: linear-gradient(135deg, var(--bg2) 0%, var(--bg3) 100%);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .card-title {
            font-size: 14px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid var(--border);
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
        
        .stat-label {
            color: var(--text2);
        }
        
        .stat-value {
            color: var(--text);
            font-weight: 600;
        }
        
        .signal-box {
            background: rgba(0, 255, 136, 0.1);
            border-left: 3px solid var(--green);
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
            font-size: 12px;
        }
        
        .signal-box.buy {
            border-left-color: var(--green);
            background: rgba(0, 255, 136, 0.1);
        }
        
        .signal-box.sell {
            border-left-color: var(--red);
            background: rgba(255, 68, 102, 0.1);
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .status-badge.active {
            background: rgba(0, 255, 136, 0.2);
            color: var(--green);
        }
        
        .status-badge.inactive {
            background: rgba(255, 68, 102, 0.2);
            color: var(--red);
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid var(--border);
            color: var(--text2);
            font-size: 11px;
        }
        
        .last-update {
            text-align: center;
            color: var(--text2);
            font-size: 11px;
            margin-top: 10px;
        }
        
        @media (max-width: 768px) {
            .bot-grid {
                grid-template-columns: 1fr;
            }
            
            .tabs {
                overflow-x: auto;
            }
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
            <div class="status-item">
                <div class="status-dot active"></div>
                <span>PS2TRADEB: <span id="status-ps2tradeb">ACTIVE</span></span>
            </div>
            <div class="status-item">
                <div class="status-dot active"></div>
                <span>BTBOT: <span id="status-btbot">ACTIVE</span></span>
            </div>
            <div class="status-item">
                <div class="status-dot active"></div>
                <span>ETBOT: <span id="status-etbot">ACTIVE</span></span>
            </div>
            <div class="status-item">
                <div class="status-dot active"></div>
                <span>ATBOT: <span id="status-atbot">ACTIVE</span></span>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('all')">📊 ALL BOTS</button>
            <button class="tab-button" onclick="switchTab('ps2tradeb')">🟢 PS2TRADEB</button>
            <button class="tab-button" onclick="switchTab('btbot')">🟠 BTBOT</button>
            <button class="tab-button" onclick="switchTab('etbot')">🔵 ETBOT</button>
            <button class="tab-button" onclick="switchTab('atbot')">🟠 ATBOT</button>
        </div>
        
        <!-- ALL BOTS TAB -->
        <div id="all" class="tab-content active">
            <div class="bot-grid">
                <div class="card">
                    <div class="card-title ps2tradeb">🟢 PS2TRADEB v5.0</div>
                    <div class="stat-row">
                        <span class="stat-label">Exchange:</span>
                        <span class="stat-value">Binance LIVE</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Algorithm:</span>
                        <span class="stat-value">Multi-Factor</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value"><span class="status-badge active">ACTIVE</span></span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Pairs:</span>
                        <span class="stat-value">5</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Risk/Trade:</span>
                        <span class="stat-value">1.0%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Signal:</span>
                        <span class="stat-value" id="ps2-signal">--</span>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title btbot">🟠 BTBOT v5.0</div>
                    <div class="stat-row">
                        <span class="stat-label">Exchange:</span>
                        <span class="stat-value">Binance LIVE</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Algorithm:</span>
                        <span class="stat-value">RSI Strategy</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value"><span class="status-badge active">ACTIVE</span></span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Pairs:</span>
                        <span class="stat-value">5</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Risk/Trade:</span>
                        <span class="stat-value">0.5%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Signal:</span>
                        <span class="stat-value" id="btbot-signal">--</span>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title etbot">🔵 ETBOT v5.0</div>
                    <div class="stat-row">
                        <span class="stat-label">API:</span>
                        <span class="stat-value">CoinGecko</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Algorithm:</span>
                        <span class="stat-value">Momentum</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value"><span class="status-badge active">ACTIVE</span></span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Symbols:</span>
                        <span class="stat-value">2</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Risk/Trade:</span>
                        <span class="stat-value">0.3%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Signal:</span>
                        <span class="stat-value" id="etbot-signal">--</span>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title atbot">🟠 ATBOT v5.2</div>
                    <div class="stat-row">
                        <span class="stat-label">Exchange:</span>
                        <span class="stat-value">Alpaca LIVE</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Algorithm:</span>
                        <span class="stat-value">Multi-Factor</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Status:</span>
                        <span class="stat-value"><span class="status-badge active">ACTIVE</span></span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Pairs:</span>
                        <span class="stat-value">5</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Risk/Trade:</span>
                        <span class="stat-value">1.0%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Last Signal:</span>
                        <span class="stat-value" id="atbot-signal">--</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- PS2TRADEB TAB -->
        <div id="ps2tradeb" class="tab-content">
            <div class="bot-grid">
                <div class="card">
                    <div class="card-title ps2tradeb">🟢 PS2TRADEB v5.0 - DETAILED</div>
                    <div class="stat-row">
                        <span class="stat-label">Exchange:</span>
                        <span class="stat-value">Binance LIVE</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Algorithm:</span>
                        <span class="stat-value">24h Change + RSI (15m)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Pairs:</span>
                        <span class="stat-value">BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, XRPUSDT</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Risk/Trade:</span>
                        <span class="stat-value">1.0% of account</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Stop Loss:</span>
                        <span class="stat-value">2.0%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Take Profit:</span>
                        <span class="stat-value">3.0%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Daily Max Loss:</span>
                        <span class="stat-value">5%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Position Limit:</span>
                        <span class="stat-value">5 concurrent</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Telegram:</span>
                        <span class="stat-value">@ps2TradeB_bot</span>
                    </div>
                    <div class="signal-box buy">
                        📊 Last Signal: <strong id="ps2-detail-signal">Monitoring...</strong>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- BTBOT TAB -->
        <div id="btbot" class="tab-content">
            <div class="bot-grid">
                <div class="card">
                    <div class="card-title btbot">🟠 BTBOT v5.0 - DETAILED</div>
                    <div class="stat-row">
                        <span class="stat-label">Exchange:</span>
                        <span class="stat-value">Binance LIVE</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Algorithm:</span>
                        <span class="stat-value">RSI (14-period, 15m candles)</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Pairs:</span>
                        <span class="stat-value">BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, XRPUSDT</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Risk/Trade:</span>
                        <span class="stat-value">0.5% of account</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Stop Loss:</span>
                        <span class="stat-value">1.5%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Take Profit:</span>
                        <span class="stat-value">2.5%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Daily Max Loss:</span>
                        <span class="stat-value">3%</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Position Limit:</span>
                        <span class="stat-value">3 concurrent</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Telegram:</span>
                        <span class="stat-value">@binance_bt_bot</span>
                    </div>
                    <div class="signal-box buy">
                        📊 Last Signal: <strong id="btbot-detail-signal">Monitoring...</strong>
                    </div>
                </div>
