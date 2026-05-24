# strategy.py — 3 trading strategies for btbot / ps1trade
# Strategy 1: RSI Oversold  → RSI < 42 → TP 2.0% | SL 0.5%
# Strategy 2: SMA Crossover → price > SMA20, 45<RSI<75 → TP 1.5%
# Strategy 3: MACD Cross    → MACD crosses above signal → TP 1.5%

import pandas as pd
import numpy as np
from logger import log
import config


def _rsi(series: pd.Series, period: int = 14) -> float:
    if len(series) < period + 1:
        return 50.0
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(com=period - 1, adjust=True).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period - 1, adjust=True).mean()
    rs    = gain / loss.replace(0, np.inf)
    val   = (100 - 100 / (1 + rs)).iloc[-1]
    return round(float(val) if not np.isnan(val) else 50.0, 2)


def _sma(series: pd.Series, period: int) -> float:
    return float(series.tail(period).mean())


def _macd(series: pd.Series):
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    macd  = ema12 - ema26
    signal= macd.ewm(span=9, adjust=False).mean()
    return macd, signal


def detect_signal(symbol: str, df: pd.DataFrame) -> dict:
    """Returns signal dict. signal=True means open a trade."""
    no_sig = {"signal": False, "strength": 0.0, "reason": "No signal",
               "tp_pct": 0.0, "sl_pct": config.STOP_LOSS_PCT,
               "strategy": "NONE", "rsi": 0.0, "price": 0.0}

    if df is None or len(df) < 30:
        return no_sig

    try:
        close  = df['close'].astype(float).reset_index(drop=True)
        price  = float(close.iloc[-1])
        rsi    = _rsi(close)
        sma20  = _sma(close, 20)
        sma50  = _sma(close, 50)

        macd_line, signal_line = _macd(close)
        macd_now   = float(macd_line.iloc[-1])
        macd_prev  = float(macd_line.iloc[-2])
        signal_now = float(signal_line.iloc[-1])
        signal_prev= float(signal_line.iloc[-2])

        # ─ Strategy 1: RSI Oversold ──────────────────────────────────
        if rsi < config.RSI_OVERSOLD:
            strength = round(min(0.97, 0.72 + (config.RSI_OVERSOLD - rsi) / 30), 4)
            if strength >= config.MIN_SIGNAL_STR:
                log.info(f"[SIGNAL] {symbol} RSI_OVERSOLD | RSI={rsi} str={strength:.0%}")
                return {"signal": True, "strength": strength,
                        "reason": f"RSI Oversold ({rsi:.1f})",
                        "tp_pct": config.TP_RSI_OVERSOLD,
                        "sl_pct": config.STOP_LOSS_PCT,
                        "strategy": "RSI_OVERSOLD", "rsi": rsi, "price": price}

        # ─ Strategy 2: SMA Crossover ─────────────────────────────────
        if price > sma20 and config.RSI_SMA_LOW < rsi < config.RSI_SMA_HIGH:
            # Extra confirmation: SMA20 > SMA50 (uptrend)
            trend_up  = sma20 > sma50
            strength  = round(min(0.95, 0.72 + (rsi - config.RSI_SMA_LOW) / 80), 4)
            if trend_up:
                strength = round(min(0.97, strength + 0.05), 4)
            if strength >= config.MIN_SIGNAL_STR:
                log.info(f"[SIGNAL] {symbol} SMA_CROSS | RSI={rsi} str={strength:.0%}")
                return {"signal": True, "strength": strength,
                        "reason": f"Above SMA20, RSI={rsi:.1f}",
                        "tp_pct": config.TP_SMA_CROSS,
                        "sl_pct": config.STOP_LOSS_PCT,
                        "strategy": "SMA_CROSS", "rsi": rsi, "price": price}

        # ─ Strategy 3: MACD Crossover ────────────────────────────────
        macd_crossed_up = macd_prev < signal_prev and macd_now > signal_now
        if macd_crossed_up and rsi < 72:
            strength = round(min(0.92, 0.74 + abs(macd_now - signal_now) * 2), 4)
            if strength >= config.MIN_SIGNAL_STR:
                log.info(f"[SIGNAL] {symbol} MACD_CROSS | RSI={rsi} str={strength:.0%}")
                return {"signal": True, "strength": strength,
                        "reason": f"MACD bullish cross, RSI={rsi:.1f}",
                        "tp_pct": config.TP_MACD_CROSS,
                        "sl_pct": config.STOP_LOSS_PCT,
                        "strategy": "MACD_CROSS", "rsi": rsi, "price": price}

        log.debug(f"[SIGNAL] {symbol} NONE | RSI={rsi:.1f} price={price:.4f} sma20={sma20:.4f}")
        return {**no_sig, "rsi": rsi, "price": price}

    except Exception as e:
        log.error(f"[SIGNAL] {symbol} error: {e}")
        return no_sig
