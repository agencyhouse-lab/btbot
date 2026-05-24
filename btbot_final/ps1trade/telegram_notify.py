# telegram_notify.py — Telegram alerts
import requests, config
from logger import log

_BASE = f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}"
TAG   = config.BOT_TAG


def send(text: str, silent: bool = False) -> bool:
    try:
        r = requests.post(f"{_BASE}/sendMessage", json={
            "chat_id": config.TELEGRAM_CHAT_ID, "text": text,
            "parse_mode": "Markdown", "disable_notification": silent,
        }, timeout=10)
        return r.status_code == 200
    except Exception as e:
        log.error(f"[TG] {e}"); return False


def test_ok() -> bool:
    try:
        r = requests.get(f"{_BASE}/getMe", timeout=8)
        if r.ok:
            name = r.json()['result']['username']
            log.info(f"[TG] @{name} connected")
            return True
    except Exception as e:
        log.error(f"[TG] test failed: {e}")
    return False


def started(balance: float, mode: str):
    icon = "🔴" if mode == "live" else "📄"
    send(f"{TAG} {icon} *{config.BOT_NAME} v{config.BOT_VERSION} Started*\n"
         f"━━━━━━━━━━━━━━━━━\n"
         f"💰 Balance: `${balance:,.2f}`\n"
         f"📊 Mode: `{mode.upper()}`\n"
         f"🔍 Pairs: `{len(config.SYMBOLS)}`\n"
         f"🛑 SL: `0.5%` | 🎯 TP: `1.5–2%`\n"
         f"⚠️ Risk: `0.25%/trade` | Max: `5 trades`\n"
         f"━━━━━━━━━━━━━━━━━\n"
         f"_Scanning market now..._")


def stopped(reason: str):
    send(f"{TAG} 🔴 *{config.BOT_NAME} STOPPED*\n`{reason}`\n"
         f"_Restart: `systemctl start {config.BOT_NAME}`_")


def trade_opened(sym, entry, qty, tp, sl, strategy, strength, reason):
    send(f"{TAG} ✅ *TRADE OPENED*\n"
         f"━━━━━━━━━━━━━━━━━\n"
         f"💱 `{sym}`\n"
         f"📥 Entry:  `${entry:,.6f}`\n"
         f"📦 Qty:    `{qty}`\n"
         f"🎯 TP:     `${tp:,.6f}`\n"
         f"🛑 SL:     `${sl:,.6f}`\n"
         f"━━━━━━━━━━━━━━━━━\n"
         f"📊 `{strategy}` | 💪 `{strength:.0%}`\n"
         f"_{reason}_")


def trade_closed_tp(sym, entry, exit_p, pnl_u, pnl_p):
    send(f"{TAG} 💰 *TAKE PROFIT* 🎉\n"
         f"━━━━━━━━━━━━━━━━━\n"
         f"💱 `{sym}`\n"
         f"📥 `${entry:,.6f}` → 📤 `${exit_p:,.6f}`\n"
         f"📈 `+{pnl_p:.2f}%` | `+${pnl_u:.4f} USDT`")


def trade_closed_sl(sym, entry, exit_p, pnl_u, pnl_p):
    send(f"{TAG} 🛑 *STOP LOSS*\n"
         f"💱 `{sym}`\n"
         f"📥 `${entry:,.6f}` → 📤 `${exit_p:,.6f}`\n"
         f"📉 `-{abs(pnl_p):.2f}%` | `-${abs(pnl_u):.4f} USDT`")


def market_bad(score, failing):
    send(f"{TAG} ⏳ *Market Not Ready* `{score}`\n"
         f"_{', '.join(failing)}_", silent=True)


def hourly(stats: dict, open_trades: dict):
    pos = "\n".join(
        f"  {'📈' if (v.get('current',v['entry_price'])-v['entry_price'])>=0 else '📉'}"
        f" `{k}`: `{((v.get('current',v['entry_price'])-v['entry_price'])/v['entry_price']*100):+.2f}%`"
        for k, v in open_trades.items()
    ) or "  _None_"
    send(f"{TAG} 📊 *Hourly Report*\n"
         f"━━━━━━━━━━━━━━━━━\n"
         f"💰 `{stats['balance']}`\n"
         f"📅 Day: `{stats['day_pnl']}` | Total: `{stats['total_pnl']}`\n"
         f"🏆 Win: `{stats['win_rate']}` ({stats['wins']}W/{stats['losses']}L)\n"
         f"📦 Open:\n{pos}", silent=True)


def error(msg: str):
    send(f"{TAG} 🚨 *ERROR — BOT STOPPED*\n"
         f"```\n{str(msg)[:400]}\n```\n"
         f"_Check: `journalctl -u {config.BOT_NAME} -n 50`_")
