# ================================================================
#  etbot — eToro Trading Bot
#  Server:    maxhive.cloud (72.62.254.237)
#  Bot:       @etoro_et_bot
#  Dashboard: http://maxhive.cloud:8080/etbot
# ================================================================

# ── TELEGRAM ─────────────────────────────────────────────────────
TELEGRAM_TOKEN   = "8882293371:AAFJMkVLKQBJw6eBW9rS69_oQ3k7VIv_0Ls"
TELEGRAM_CHAT_ID = "5587885687"
BOT_NAME         = "🏦 eToro Bot"
BOT_HANDLE       = "@etoro_et_bot"

# ── CAPITAL ──────────────────────────────────────────────────────
STARTING_CAPITAL      = 1000.0
REINVEST_PROFIT_RATIO = 0.80    # 80% of profits reinvested
WITHDRAW_RATIO        = 0.20    # 20% available to withdraw

# ── RISK RULES ───────────────────────────────────────────────────
RISK_PER_TRADE  = 0.0025   # 0.25% risk per trade (locked)
STOP_LOSS_PCT   = 0.001    # 0.10% stop loss
MAX_OPEN_TRADES = 5

# ── NEWS-BASED POSITION SIZING ───────────────────────────────────
NEWS_SIZE_STRONG  = 1.5    # Score >= 3 → 1.5x position
NEWS_SIZE_NORMAL  = 1.0    # Score 0-2 → 1.0x position
NEWS_SIZE_WEAK    = 0.5    # Score < 0 → 0.5x (or skip)
NEWS_SCORE_STRONG = 3

# ── CAPITAL ALLOCATION (based on market sentiment) ───────────────
ALLOC_BULL_MARKET = 0.70   # Good market  → deploy 70%
ALLOC_NEUTRAL     = 0.50   # Neutral      → deploy 50%
ALLOC_BEAR_MARKET = 0.20   # Bad market   → deploy 20%
MIN_RESERVE_PCT   = 0.30   # Always keep 30% safe minimum

# ── TAKE PROFIT (per strategy) ────────────────────────────────────
TP_RSI_OVERSOLD  = 0.02    # RSI strategy  → +2.0%
TP_SMA_CROSSOVER = 0.015   # SMA strategy  → +1.5%

# ── SIGNAL THRESHOLDS ────────────────────────────────────────────
MIN_SIGNAL_STRENGTH = 0.80
RSI_OVERSOLD_LEVEL  = 35
RSI_SMA_LOW         = 50
RSI_SMA_HIGH        = 70

# ── TIMING ───────────────────────────────────────────────────────
SCAN_INTERVAL_MINUTES = 2    # Scan every 2 minutes (market hours only)
EXIT_CHECK_SECONDS    = 30   # Check exits every 30 seconds (always)
NEWS_REPORT_HOURS     = 6    # Full news report every 6 hours
DAY_END_HOUR          = 16   # 4 PM ET day-end report

# ── WATCHLIST (14 assets) ────────────────────────────────────────
STOCKS      = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
ETFS        = ["SPY", "QQQ", "IWM", "DIA"]
COMMODITIES = ["GLD", "SLV", "USO", "GDX"]
ALL_SYMBOLS = STOCKS + ETFS + COMMODITIES

COMMODITY_NAMES = {
    "GLD": "Gold ETF", "SLV": "Silver ETF",
    "USO": "Oil ETF",  "GDX": "Gold Miners ETF"
}

# ── SERVER ───────────────────────────────────────────────────────
SERVER_HOST      = "maxhive.cloud"
DASHBOARD_PORT   = 8080
DASHBOARD_PASS   = "etbot2026"

# ── FILE PATHS ────────────────────────────────────────────────────
BASE_DIR   = "/root/etoro"
STATE_FILE = "/root/etoro/data/etbot_state.json"
LOG_FILE   = "/root/etoro/logs/etbot.log"
