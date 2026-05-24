# config.py — shared config for btbot & ps1trade
import os
from dotenv import load_dotenv

_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(_DIR, '.env'), override=True)

# ── Identity ──────────────────────────────────────────────────────────
BOT_MODE    = os.getenv("BOT_MODE",   "paper")    # "live" or "paper"
BOT_NAME    = os.getenv("BOT_NAME",   "btbot")
BOT_TAG     = os.getenv("BOT_TAG",    "🤖[BOT]")
BOT_VERSION = "2.1.0"
IS_LIVE     = BOT_MODE == "live"

# ── Binance ───────────────────────────────────────────────────────────
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY",    "").strip()
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "").strip()
BINANCE_TESTNET    = os.getenv("BINANCE_TESTNET", "true").lower() == "true"

# ── Telegram ──────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

# ── Symbols (10 crypto pairs) ─────────────────────────────────────────
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT",
    "XRPUSDT", "DOTUSDT", "LINKUSDT", "LTCUSDT", "MATICUSDT",
]

# ── Risk (LOCKED) ─────────────────────────────────────────────────────
RISK_PER_TRADE  = float(os.getenv("RISK_PER_TRADE", "0.0025"))  # 0.25%
STOP_LOSS_PCT   = float(os.getenv("STOP_LOSS_PCT",  "0.005"))   # 0.5%
MAX_OPEN_TRADES = int(os.getenv("MAX_OPEN_TRADES",  "5"))
STARTING_BALANCE= float(os.getenv("STARTING_BALANCE","1000.0"))

# ── Take Profit per strategy ──────────────────────────────────────────
TP_RSI_OVERSOLD  = 0.020   # 2.0%
TP_SMA_CROSS     = 0.015   # 1.5%
TP_MACD_CROSS    = 0.015   # 1.5%

# ── Signal thresholds (relaxed to allow real trades) ──────────────────
MIN_SIGNAL_STR   = 0.72    # Was 0.80 — too strict, caused 0 trades
MIN_MARKET_SCORE = 5       # Was 6/8 — blocked too often in sideways
ADX_MIN          = 20      # Was 25 — crypto trends start at lower ADX

# RSI thresholds (relaxed)
RSI_OVERSOLD     = 42      # Was 35 — too rare, now catches more pullbacks
RSI_SMA_LOW      = 45      # Was 50
RSI_SMA_HIGH     = 75      # Was 70

# ── Timing ────────────────────────────────────────────────────────────
SCAN_INTERVAL_SEC = 120    # Scan every 2 min
EXIT_CHECK_SEC    = 30     # Check TP/SL every 30 sec
KLINE_LOOKBACK    = "5 days ago UTC"

# ── Paths ─────────────────────────────────────────────────────────────
_DIR       = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(_DIR, f"{BOT_NAME}_state.json")
LOG_DIR    = os.path.join(_DIR, "logs")
