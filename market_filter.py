# market_filter.py — Market health check (5/8 conditions needed)
import pandas as pd
import numpy as np
from logger import log
import config


def check_market(df: pd.DataFrame) -> dict:
    """
    Check 8 market conditions.
    Need 5+ to allow trading (relaxed from 6 — was blocking all trades).
    Returns dict with tradeable=True/False and details.
    """
    if df is None or len(df) < 50:
        return {"tradeable": False, "score": "0/8", "status": "NO_DATA",
                "conditions": {}, "rsi": 0, "adx": 0}
    try:
        close = df['close'].astype(float)
        high  = df['high'].astype(float)
        low   = df['low'].astype(float)
        vol   = df['volume'].astype(float)

        # ── EMA 20 / 50 / 200 ─────────────────────────────────────────
        ema20  = float(close.ewm(span=20).mean().iloc[-1])
        ema50  = float(close.ewm(span=50).mean().iloc[-1])
        ema200 = float(close.ewm(span=200).mean().iloc[-1]) if len(close)>=200 else ema50
        price  = float(close.iloc[-1])

        # ── RSI ────────────────────────────────────────────────────────
        delta = close.diff()
        gain  = delta.clip(lower=0).ewm(com=13).mean()
        loss  = (-delta.clip(upper=0)).ewm(com=13).mean()
        rsi   = float((100 - 100/(1 + gain/loss.replace(0,np.inf))).iloc[-1])

        # ── ADX (simplified) ───────────────────────────────────────────
        tr    = pd.concat([high - low,
                           (high - close.shift()).abs(),
                           (low  - close.shift()).abs()], axis=1).max(axis=1)
        atr14 = float(tr.ewm(span=14).mean().iloc[-1])
        # Use price change as ADX proxy if ta library not available
        changes= close.pct_change().abs().tail(14)
        adx_proxy = float(changes.mean() * 100 * 20)   # Scale to ADX range

        # ── Volume ─────────────────────────────────────────────────────
        vol_ma  = float(vol.rolling(20).mean().iloc[-1])
        vol_now = float(vol.iloc[-1])

        # ── Bollinger Width ────────────────────────────────────────────
        sma20   = float(close.rolling(20).mean().iloc[-1])
        std20   = float(close.rolling(20).std().iloc[-1])
        bb_width= (4 * std20) / sma20 if sma20 > 0 else 0

        # ── ATR % ─────────────────────────────────────────────────────
        atr_pct = atr14 / price if price > 0 else 0

        # ── 8 Conditions ───────────────────────────────────────────────
        conditions = {
            "trend_exists":  adx_proxy > config.ADX_MIN,       # Relaxed: 20 not 25
            "not_overbought":rsi < 80,                          # RSI not extreme
            "price_above_ema20": price > ema20 * 0.995,        # Allow 0.5% below
            "ema20_above_ema50": ema20 > ema50 * 0.998,        # Allow slight gap
            "volatility_ok": atr_pct < 0.05,                   # ATR < 5% (crypto)
            "bb_has_room":   bb_width > 0.01,                  # Room to move
            "volume_ok":     vol_now > vol_ma * 0.6,           # 60% of avg vol
            "no_crash":      close.pct_change().tail(3).min() > -0.05,  # No -5% candle
        }

        score  = sum(conditions.values())
        status = ("EXCELLENT" if score >= 7 else
                  "GOOD"      if score >= 5 else
                  "NEUTRAL"   if score >= 3 else "BAD")

        tradeable = score >= config.MIN_MARKET_SCORE
        failing   = [k for k, v in conditions.items() if not v]
        if failing:
            log.debug(f"[MARKET] Score {score}/8 | Failing: {failing}")

        return {
            "tradeable":  tradeable,
            "score":      f"{score}/8",
            "status":     status,
            "conditions": conditions,
            "rsi":        round(rsi, 1),
            "adx":        round(adx_proxy, 1),
            "failing":    failing,
        }
    except Exception as e:
        log.error(f"[MARKET] Check error: {e}")
        return {"tradeable": True, "score": "?/8", "status": "ERROR",
                "conditions": {}, "rsi": 0, "adx": 0, "failing": []}
