#!/usr/bin/env python3
"""
etbot.py — eToro Trading Bot | @etoro_et_bot
Server: maxhive.cloud | Dashboard: http://maxhive.cloud:8080/etbot

4 Threads:
  ScanLoop    — every 2 min, market hours only
  ExitLoop    — every 30s, always active
  ReportsLoop — hourly heartbeat + 6h news + day-end
  TelegramPoll— listens for /et_ commands
"""

import time, threading, traceback
from datetime import datetime
from etbot_config import (
    TELEGRAM_CHAT_ID, ALL_SYMBOLS,
    SCAN_INTERVAL_MINUTES, EXIT_CHECK_SECONDS,
    NEWS_REPORT_HOURS, DAY_END_HOUR
)
from signal_engine import detect_signal, get_current_price, is_market_open, get_market_status
from news_engine   import analyze_macro_news, build_6hour_report
from trade_manager import TradeManager
from notifier      import send_telegram, get_updates
from logger        import logger

manager     = TradeManager()
bot_running = True
tg_offset   = 0


# ─── SCAN ────────────────────────────────────────────────────────
def run_scan():
    if manager.bot_paused or not bot_running:
        return
    mkt = get_market_status()
    if not mkt["open"]:
        logger.info(f"Market {mkt['status']} ({mkt['day']} {mkt['time_et']}) — skip")
        return

    logger.info(f"── Scan {mkt['time_et']} ──")
    macro = analyze_macro_news()
    logger.info(f"  Macro: {macro['sentiment']} score={macro['score']:+d}")

    if not macro["trade_ok"]:
        send_telegram(
            f"🌍 *Market too risky — no new trades*\n\n"
            f"Sentiment: `{macro['sentiment']}`  Score: `{macro['score']:+d}`\n"
            f"Deploy max: `${manager.total_capital*macro['alloc_pct']:.2f}` ({macro['alloc_pct']*100:.0f}%)\n"
            f"Protected:  `${manager.total_capital*macro['reserve_pct']:.2f}` ({macro['reserve_pct']*100:.0f}%)",
            "WARNING"
        )

    found = 0
    for symbol in ALL_SYMBOLS:
        if not bot_running or manager.bot_paused: break
        if symbol in manager.open_trades: continue
        if len(manager.open_trades) >= 5: break
        try:
            signal = detect_signal(symbol, macro_news=macro)
            if signal and manager.open_trade(signal):
                found += 1
        except Exception as e:
            logger.error(f"Signal error {symbol}: {e}")
    logger.info(f"── Scan done. New={found} Open={len(manager.open_trades)} ──")


# ─── EXIT MONITOR ────────────────────────────────────────────────
def run_exit_check():
    if manager.open_trades:
        manager.monitor_trades()


# ─── NEWS REPORT ─────────────────────────────────────────────────
def send_news_report():
    logger.info("Building 6h news report...")
    try:
        report = build_6hour_report(
            capital=manager.total_capital, open_trades=manager.open_trades,
            profit=manager.total_profit, loss=manager.total_loss,
            total_trades=manager.total_trades, daily_pnl=manager.daily_pnl
        )
        # Split if too long (Telegram 4096 char limit)
        if len(report) > 3800:
            parts, chunk = [], ""
            for line in report.split("\n"):
                if len(chunk)+len(line)+1 < 3800:
                    chunk += line+"\n"
                else:
                    if chunk.strip(): parts.append(chunk.strip())
                    chunk = line+"\n"
            if chunk.strip(): parts.append(chunk.strip())
            for i, part in enumerate(parts):
                send_telegram(part, "REPORT")
                if i < len(parts)-1: time.sleep(1)
        else:
            send_telegram(report, "REPORT")
        logger.info("6h news report sent.")
    except Exception as e:
        logger.error(f"News report error: {e}")
        send_telegram(f"⚠️ News report failed: `{e}`", "ERROR")


# ─── TELEGRAM COMMANDS ───────────────────────────────────────────
def handle_command(text: str, chat_id: str):
    global bot_running
    if str(chat_id) != str(TELEGRAM_CHAT_ID): return
    cmd = text.strip().lower().split()[0]

    if cmd in ("/et_start", "/et_help"):
        mkt = get_market_status()
        send_telegram(
            f"🤖 *eToro Bot Commands*\n\n"
            f"Market: {mkt['status']} | {mkt['day']} {mkt['time_et']}\n\n"
            "`/et_status`   — Portfolio & P&L\n"
            "`/et_trades`   — Open trades live\n"
            "`/et_news`     — News report now\n"
            "`/et_scan`     — Force market scan\n"
            "`/et_history`  — Last 10 trades\n"
            "`/et_market`   — Market status\n"
            "`/et_pause`    — Pause trading\n"
            "`/et_resume`   — Resume trading\n"
            "`/et_stop`     — Emergency stop\n\n"
            f"🌐 Dashboard: http://maxhive.cloud:8080/etbot", "INFO"
        )

    elif cmd == "/et_status":
        prices = {s: p for s in manager.open_trades if (p := get_current_price(s))}
        mkt    = get_market_status()
        summary = manager.status_summary(prices)
        summary += f"\n\n🕐 Market: {mkt['status']} | {mkt['time_et']}"
        send_telegram(summary, "REPORT")

    elif cmd == "/et_trades":
        if not manager.open_trades:
            send_telegram("📂 No open trades right now.", "INFO"); return
        lines = ["📂 *Open Trades:*\n"]
        for sym, t in manager.open_trades.items():
            price = get_current_price(sym) or t["entry_price"]
            pct   = (price - t["entry_price"]) / t["entry_price"] * 100
            try:
                held = (datetime.now() - datetime.fromisoformat(t["entry_time"])).seconds//3600
            except Exception:
                held = 0
            lines.append(
                f"{'🟢'if pct>=0 else '🔴'} *{sym}*\n"
                f"  Now:`${price:.2f}` ({pct:+.2f}%) Held:`{held}h`\n"
                f"  Entry:`${t['entry_price']:.2f}` "
                f"SL:`${t['stop_loss']:.4f}` TP:`${t['take_profit']:.4f}`\n"
                f"  Signal:`{t['signal_strength']*100:.0f}%` "
                f"News:`{t.get('news_score',0):+d}` "
                f"Size:`{t.get('position_mult',1)}x`\n"
            )
        send_telegram("\n".join(lines), "INFO")

    elif cmd == "/et_news":
        send_telegram("📰 Generating news report...", "INFO")
        threading.Thread(target=send_news_report, daemon=True).start()

    elif cmd == "/et_market":
        mkt = get_market_status()
        send_telegram(
            f"🕐 *Market Status*\n\n"
            f"Status: {mkt['status']}\n"
            f"Day:    `{mkt['day']}`\n"
            f"Time:   `{mkt['time_et']}`\n\n"
            f"Hours: Mon–Fri 09:30–16:00 ET\n"
            f"_Scanning only during market hours_", "INFO"
        )

    elif cmd == "/et_scan":
        mkt = get_market_status()
        if not mkt["open"]:
            send_telegram(
                f"⏰ Market is {mkt['status']}\n{mkt['day']} {mkt['time_et']}\n\n"
                f"Scanning starts Monday 09:30 ET.\n"
                f"Use `/et_news` for analysis anytime.", "INFO"); return
        send_telegram("🔍 Running scan now...", "INFO")
        threading.Thread(target=_safe_scan, daemon=True).start()

    elif cmd == "/et_history":
        recent = manager.trade_history[-10:]
        if not recent:
            send_telegram("📋 No trade history yet.", "INFO"); return
        lines  = ["📋 *Last 10 Trades:*\n"]
        net_10 = sum(h["pnl"] for h in recent)
        wins   = sum(1 for h in recent if h["pnl"] > 0)
        for h in reversed(recent):
            lines.append(
                f"{'✅'if h['pnl']>=0 else '❌'} *{h['symbol']}*: "
                f"`{h['pnl']:+.2f}$` ({h['pnl_pct']:+.2f}%) {h['reason']}\n"
                f"  News:`{h.get('news_score',0):+d}` Size:`{h.get('pos_mult',1)}x` "
                f"`{str(h.get('timestamp',''))[:16]}`"
            )
        lines.append(f"\n📊 Net: `{net_10:+.2f}$`  Win rate: `{wins}/10`")
        send_telegram("\n".join(lines), "REPORT")

    elif cmd == "/et_pause":
        manager.bot_paused = True; manager.save()
        send_telegram("⛔ *Bot Paused*\nNo new trades. Open trades still monitored.\nUse `/et_resume` to continue.", "STOP")

    elif cmd == "/et_resume":
        manager.bot_paused = False; manager.save()
        send_telegram("▶️ *Bot Resumed* — Scanning for trades.", "INFO")

    elif cmd == "/et_stop":
        bot_running = False; manager.bot_paused = True; manager.save()
        send_telegram(
            f"🛑 *EMERGENCY STOP*\n"
            f"Open trades: `{len(manager.open_trades)}`\n"
            "⚠️ *Check eToro — close positions manually!*", "STOP"
        )


def telegram_poll_loop():
    global tg_offset
    logger.info("Telegram poll loop started.")
    while bot_running:
        try:
            for upd in get_updates(offset=tg_offset):
                tg_offset = upd["update_id"] + 1
                msg  = upd.get("message", {})
                text = msg.get("text", "")
                cid  = str(msg.get("chat", {}).get("id", ""))
                if text.startswith("/et"):
                    handle_command(text, cid)
        except Exception as e:
            logger.error(f"Poll error: {e}")
        time.sleep(2)


# ─── SCHEDULER LOOPS ─────────────────────────────────────────────
def _safe_scan():
    try:
        run_scan()
    except Exception as e:
        logger.error(f"Scan crash: {e}")
        send_telegram(f"🚨 *Scan crashed!*\n`{str(e)}`\n```{traceback.format_exc()[-300:]}```", "ERROR")

def scan_loop():
    while bot_running:
        _safe_scan()
        for _ in range(SCAN_INTERVAL_MINUTES * 60):
            if not bot_running: break
            time.sleep(1)

def exit_loop():
    while bot_running:
        try:
            run_exit_check()
        except Exception as e:
            logger.error(f"Exit error: {e}")
        for _ in range(EXIT_CHECK_SECONDS):
            if not bot_running: break
            time.sleep(1)

def reports_loop():
    last_news_h, last_beat_h, last_day_end = -1, -1, -1
    while bot_running:
        now  = datetime.now()
        hour = now.hour

        if hour % NEWS_REPORT_HOURS == 0 and hour != last_news_h:
            last_news_h = hour
            threading.Thread(target=send_news_report, daemon=True).start()

        if hour != last_beat_h:
            last_beat_h = hour
            mkt = get_market_status()
            net = manager.total_profit - manager.total_loss
            hrs = NEWS_REPORT_HOURS - (hour % NEWS_REPORT_HOURS)
            send_telegram(
                f"💓 *Hourly Update*\n\n"
                f"🕐 Market: {mkt['status']} | {mkt['time_et']}\n"
                f"💼 Capital:  `${manager.total_capital:.2f}`\n"
                f"📊 Net P&L:  `{net:+.2f}$`\n"
                f"📅 Today:    `{manager.daily_pnl:+.2f}$`\n"
                f"📂 Open:     `{len(manager.open_trades)}/5`\n"
                f"🤖 Status:   `{'PAUSED ⛔'if manager.bot_paused else 'ACTIVE ✅'}`\n"
                f"📰 News in:  `{hrs}h`\n"
                f"🌐 Dashboard: http://maxhive.cloud:8080/etbot", "ALIVE"
            )

        if hour == DAY_END_HOUR and hour != last_day_end:
            last_day_end = hour
            manager.day_end_report()

        time.sleep(58)


# ─── MAIN ────────────────────────────────────────────────────────
def main():
    global bot_running
    logger.info("══ etbot starting on maxhive.cloud ══")

    mkt = get_market_status()
    send_telegram(
        f"🤖 *eToro Bot Started!*\n"
        f"_@etoro\\_et\\_bot | maxhive.cloud_\n\n"
        f"🕐 Market: {mkt['status']} | {mkt['time_et']}\n\n"
        f"📋 *Active Rules:*\n"
        f"📰 News gate: checked before every trade\n"
        f"📊 6-hour news + portfolio report\n"
        f"🔥 Strong news (+3) → 1.5x position\n"
        f"✅ Normal news → 1.0x position\n"
        f"🔹 Weak news → 0.5x position\n"
        f"🚫 Bad news → trade blocked\n"
        f"🛑 Stop Loss: 0.10%\n"
        f"🎯 Take Profit: 1.5%–2.0%\n"
        f"⚠️  Risk/trade: 0.25% (locked)\n"
        f"💹 Compound: 80% reinvest / 20% withdraw\n"
        f"📦 14 assets: stocks + ETFs + commodities\n\n"
        f"📱 `/et_help` for all commands\n"
        f"🌐 http://maxhive.cloud:8080/etbot", "INFO"
    )

    threads = [
        threading.Thread(target=scan_loop,         name="ScanLoop",    daemon=True),
        threading.Thread(target=exit_loop,          name="ExitLoop",    daemon=True),
        threading.Thread(target=reports_loop,       name="ReportsLoop", daemon=True),
        threading.Thread(target=telegram_poll_loop, name="TelegramPoll",daemon=True),
    ]
    for t in threads:
        t.start()
        logger.info(f"Thread started: {t.name}")

    try:
        while bot_running:
            time.sleep(5)
    except KeyboardInterrupt:
        bot_running = False
        manager.save()
        send_telegram(
            f"🛑 Bot stopped.\nOpen trades: `{len(manager.open_trades)}`\n"
            "⚠️ Monitor eToro manually.", "STOP"
        )
        logger.info("etbot stopped.")

if __name__ == "__main__":
    main()
