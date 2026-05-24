"""
signal_engine.py — Signal detection
Compatible with yfinance 0.2.40 (uses history() not fast_info)
Includes US market hours check
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import pytz

from config import (
    RSI_OVERSOLD_LEVEL, RSI_SMA_LOW, RSI_SMA_HIGH,
    MIN_SIGNAL_STRENGTH, TP_RSI_OVERSOLD, TP_SMA_CROSSOVER
)
from news_engine import analyze_symbol_news, analyze_macro_news
from logger import logger


# ── MARKET HOURS ─────────────────────────────────────────────────
def is_market_open() -> bool:
    """US market: Mon-Fri 9:30 AM – 4:00 PM ET"""
    et  = pytz.timezone("America/New_York")
    now = datetime.now(et)
    if now.weekday() >= 5:
        return False
    open_t  = now.replace(hour=9,  minute=30, second=0, microsecond=0)
    close_t = now.replace(hour=16, minute=0,  second=0, microsecond=0)
    return open_t <= now <= close_t

def get_market_status() -> dict:
    et   = pytz.timezone("America/New_York")
    now  = datetime.now(et)
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    return {
        "open":    is_market_open(),
        "status":  "🟢 OPEN" if is_market_open() else "🔴 CLOSED",
        "day":     days[now.weekday()],
        "time_et": now.strftime("%H:%M ET"),
    }


# ── PRICE FETCHING (yfinance 0.2.40 compatible) ──────────────────
def get_current_price(symbol: str) -> float | None:
    """Uses history() — works with yfinance 0.2.40 on weekends"""
    try:
        df = yf.download(symbol, period="5d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is not None and len(df) > 0:
            price = float(df["Close"].iloc[-1])
            if price > 0:
                return round(price, 4)
    except Exception:
        pass
    try:
        df2 = yf.Ticker(symbol).history(period="5d")
        if len(df2) > 0:
            return round(float(df2["Close"].iloc[-1]), 4)
    except Exception:
        pass
    return None


# ── INDICATORS ───────────────────────────────────────────────────
def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    delta = prices.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rsi   = 100 - (100 / (1 + gain / loss))
    v     = float(rsi.iloc[-1])
    return v if v == v else 50.0   # nan check

def calculate_sma(prices: pd.Series, period: int = 20) -> float:
    v = float(prices.rolling(period).mean().iloc[-1])
    return v if v == v else 0.0


# ── MAIN SIGNAL ──────────────────────────────────────────────────
def detect_signal(symbol: str, macro_news: dict = None) -> dict | None:
    logger.info(f"  Analyzing {symbol}...")

    # Gate 1: macro news
    if macro_news and not macro_news.get("trade_ok", True):
        logger.info(f"  {symbol}: blocked — macro bearish")
        return None

    # Gate 2: company news
    company_news = analyze_symbol_news(symbol)
    if not company_news["ok"]:
        logger.info(f"  {symbol}: blocked — {company_news['summary']}")
        try:
            from notifier import send_telegram
            heads = "\n".join(company_news["headlines"][:3])
            send_telegram(
                f"🚫 *{symbol} blocked by news*\n\n"
                f"Score: `{company_news['score']:+d}` | {company_news['decision']}\n"
                f"{heads}", "WARNING"
            )
        except Exception:
            pass
        return None

    # Gate 3: technical data
    try:
        df = yf.download(symbol, period="60d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is None or len(df) < 25:
            logger.warning(f"  {symbol}: not enough data")
            return None
        close         = df["Close"].squeeze()
        current_price = float(close.iloc[-1])
        rsi           = calculate_rsi(close)
        sma20         = calculate_sma(close, 20)
    except Exception as e:
        logger.error(f"  {symbol} data error: {e}")
        return None

    # Strategy 1: RSI Oversold
    signal = None
    if rsi < RSI_OVERSOLD_LEVEL:
        strength = min(0.99, 0.85 + (RSI_OVERSOLD_LEVEL - rsi) / 100)
        if strength >= MIN_SIGNAL_STRENGTH:
            signal = {"strategy":"RSI_OVERSOLD","strength":round(strength,4),
                      "profit_target":TP_RSI_OVERSOLD,"reason":f"Oversold RSI:{rsi:.0f}"}

    # Strategy 2: SMA Crossover
    elif current_price > sma20 and RSI_SMA_LOW < rsi < RSI_SMA_HIGH:
        strength = min(0.95, 0.80 + (rsi - RSI_SMA_LOW) / 100)
        if strength >= MIN_SIGNAL_STRENGTH:
            signal = {"strategy":"SMA_CROSSOVER","strength":round(strength,4),
                      "profit_target":TP_SMA_CROSSOVER,"reason":f"Above SMA20 RSI:{rsi:.0f}"}

    if not signal:
        logger.info(f"  {symbol}: no signal RSI={rsi:.1f}")
        return None

    signal.update({
        "symbol":         symbol,
        "signal":         True,
        "strength_pct":   f"{signal['strength']*100:.1f}%",
        "rsi":            round(rsi, 1),
        "sma20":          round(sma20, 4),
        "current_price":  round(current_price, 4),
        "news_score":     company_news["score"],
        "news_decision":  company_news["decision"],
        "news_summary":   company_news["summary"],
        "news_headlines": company_news["headlines"],
        "position_mult":  company_news["position_mult"],
    })
    logger.info(
        f"  {symbol} ✅ {signal['strategy']} "
        f"strength={signal['strength_pct']} "
        f"news={company_news['score']:+d} mult={company_news['position_mult']}x"
    )
    return signal
