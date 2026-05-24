"""
news_engine.py — News analysis engine
Fetches company + macro news via yfinance
Scores sentiment → trade/skip decision + position sizing
Generates 6-hour Telegram report
"""

import yfinance as yf
from datetime import datetime, timezone
from config import (
    NEWS_SIZE_STRONG, NEWS_SIZE_NORMAL, NEWS_SIZE_WEAK,
    NEWS_SCORE_STRONG, COMMODITY_NAMES,
    ALLOC_BULL_MARKET, ALLOC_NEUTRAL, ALLOC_BEAR_MARKET, MIN_RESERVE_PCT
)
from logger import logger

# ── SENTIMENT KEYWORDS ───────────────────────────────────────────
HARD_BLOCK = [
    "bankruptcy","chapter 11","criminal charges","sec charges",
    "trading halted","market crash","massive fraud","indicted",
]
STRONG_NEG = [
    "crash","crisis","collapse","recession","default","fraud","scandal",
    "investigation","layoffs","downgrade","warns","disappoints","misses",
    "below expectations","cuts guidance","plunge","selloff","sell-off",
    "tariff","sanction","conflict","attack","rate hike","inflation surge",
    "recall","hack","breach","suspended","delisted",
]
STRONG_POS = [
    "beats","record","surge","rally","upgrade","buyback","dividend",
    "partnership","acquisition","breakthrough","approved","outperform",
    "raised guidance","above expectations","profit","growth","expansion",
    "deal","contract","award","innovation","strong earnings","revenue beat",
    "bullish","momentum","recovery",
]

def score_text(text: str) -> int:
    t = text.lower()
    for kw in HARD_BLOCK:
        if kw in t: return -10
    score = 0
    for kw in STRONG_NEG:
        if kw in t: score -= 2
    for kw in STRONG_POS:
        if kw in t: score += 2
    return score

def fetch_news(symbol: str, max_items: int = 10) -> list:
    try:
        items = yf.Ticker(symbol).news or []
        now   = datetime.now(timezone.utc).timestamp()
        out   = []
        for item in items[:max_items]:
            title = (item.get("content", {}) or {}).get("title", "") or item.get("title", "")
            if not title:
                continue
            try:
                age_h = (now - float(item.get("providerPublishTime", now))) / 3600
                if age_h > 72: continue
            except Exception:
                pass
            out.append(title.strip())
        return out
    except Exception as e:
        logger.error(f"fetch_news {symbol}: {e}")
        return []

def analyze_symbol_news(symbol: str) -> dict:
    headlines = fetch_news(symbol)
    if not headlines:
        return {"symbol":symbol,"score":0,"ok":True,
                "decision":"NEUTRAL","position_mult":NEWS_SIZE_NORMAL,
                "headlines":[],"summary":"No recent news"}

    total   = sum(score_text(h) for h in headlines)
    blocked = any(score_text(h) <= -10 for h in headlines)

    if blocked or total < -3:
        decision, ok, pos_mult = "SKIP",   False, 0.0
    elif total >= NEWS_SCORE_STRONG:
        decision, ok, pos_mult = "STRONG BUY", True,  NEWS_SIZE_STRONG
    elif total >= 0:
        decision, ok, pos_mult = "BUY",    True,  NEWS_SIZE_NORMAL
    else:
        decision, ok, pos_mult = "WEAK",   True,  NEWS_SIZE_WEAK

    scored = []
    for h in headlines[:5]:
        s    = score_text(h)
        icon = "✅" if s > 0 else ("🚫" if s <= -10 else ("⚠️" if s < 0 else "➖"))
        scored.append(f"{icon} {h[:75]}")

    return {"symbol":symbol,"score":total,"ok":ok,"decision":decision,
            "position_mult":pos_mult,"headlines":scored,
            "summary":f"Score {total:+d} → {decision}"}

def analyze_macro_news() -> dict:
    total, hard_hits = 0, 0
    for proxy in ["SPY","QQQ","GLD","USO"]:
        for h in fetch_news(proxy, 8):
            s = score_text(h)
            if s <= -10: hard_hits += 1
            total += s

    if hard_hits > 0 or total < -8:
        sentiment, alloc, trade_ok = "BEARISH",    ALLOC_BEAR_MARKET, False
        outlook = "🔴 High risk — major negative events detected"
    elif total < -3:
        sentiment, alloc, trade_ok = "CAUTIOUS",   ALLOC_NEUTRAL*0.7, True
        outlook = "🟡 Cautious — deploy max 35% capital"
    elif total < 2:
        sentiment, alloc, trade_ok = "NEUTRAL",    ALLOC_NEUTRAL, True
        outlook = "🟡 Neutral — deploy max 50% capital"
    elif total < 6:
        sentiment, alloc, trade_ok = "BULLISH",    ALLOC_BULL_MARKET*0.85, True
        outlook = "🟢 Positive — deploy up to 60% capital"
    else:
        sentiment, alloc, trade_ok = "STRONG BULL",ALLOC_BULL_MARKET, True
        outlook = "🟢 Strong — deploy up to 70% capital"

    return {"sentiment":sentiment,"score":total,"hard_hits":hard_hits,
            "trade_ok":trade_ok,"alloc_pct":alloc,
            "reserve_pct":max(MIN_RESERVE_PCT, 1.0-alloc),"outlook":outlook}

def build_6hour_report(capital, open_trades, profit, loss, total_trades, daily_pnl) -> str:
    from config import STOCKS, ETFS, COMMODITIES
    macro = analyze_macro_news()
    now   = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    net   = profit - loss
    deploy_amt  = capital * macro["alloc_pct"]
    reserve_amt = capital * macro["reserve_pct"]

    L = []
    L.append(f"📰 *6-Hour Market Intelligence Report*")
    L.append(f"🕐 `{now}`\n{'─'*30}\n")
    L.append(f"💼 *Portfolio*")
    L.append(f"  Capital:  `${capital:.2f}`")
    L.append(f"  Today:    `{daily_pnl:+.2f}$`")
    L.append(f"  Net P&L:  `{net:+.2f}$`")
    L.append(f"  Trades:   `{total_trades}` | Open: `{len(open_trades)}/5`\n")
    L.append(f"🌍 *World & Economic Outlook*")
    L.append(f"  Sentiment: `{macro['sentiment']}`  Score: `{macro['score']:+d}`")
    L.append(f"  {macro['outlook']}\n")
    L.append(f"💡 *Allocation Decision*")
    L.append(f"  Deploy:  `${deploy_amt:.2f}` ({macro['alloc_pct']*100:.0f}%)")
    L.append(f"  Reserve: `${reserve_amt:.2f}` ({macro['reserve_pct']*100:.0f}%) 🔒\n")

    buy_list, skip_list = [], []
    for group, label in [(STOCKS,"📊 Stocks"),(ETFS,"📈 ETFs"),(COMMODITIES,"🪙 Commodities")]:
        L.append(f"*{label}*")
        for sym in group:
            n   = analyze_symbol_news(sym)
            tag = "HOLDING" if sym in open_trades else n["decision"]
            ic  = {"STRONG BUY":"🟢🟢","BUY":"🟢","NEUTRAL":"➖",
                   "WEAK":"🟡","SKIP":"🔴","HOLDING":"📌"}.get(tag,"➖")
            cname = COMMODITY_NAMES.get(sym,"")
            L.append(f"  {ic} *{sym}*{' ('+cname+')' if cname else ''}: `{n['summary']}`")
            if n["decision"]=="SKIP": skip_list.append(sym)
            elif n["ok"] and sym not in open_trades: buy_list.append(sym)
        L.append("")

    L.append(f"🎯 *Trade Recommendations*")
    if not macro["trade_ok"]:
        L.append("  🔴 No new trades — macro too risky. Protect capital.")
    elif buy_list:
        L.append(f"  🟢 Consider: {', '.join(buy_list[:4])}")
        if skip_list:
            L.append(f"  🔴 Avoid:    {', '.join(skip_list[:3])}")
    else:
        L.append("  ➖ No strong opportunities right now — wait.")

    L.append(f"\n_Next report in 6 hours_")
    L.append(f"_Dashboard: http://maxhive.cloud:8080/etbot_")
    return "\n".join(L)
