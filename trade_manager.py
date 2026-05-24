"""
trade_manager.py — Trade lifecycle with news-based dynamic sizing
Compound system: 80% reinvest / 20% withdraw
Losses absorbed by profit pool first
"""

import json, os
from datetime import datetime
from config import (
    STARTING_CAPITAL, RISK_PER_TRADE, STOP_LOSS_PCT,
    MAX_OPEN_TRADES, STATE_FILE,
    REINVEST_PROFIT_RATIO, WITHDRAW_RATIO, NEWS_SIZE_NORMAL
)
from notifier import send_telegram
from logger import logger


class TradeManager:

    def __init__(self):
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE) as f:
                    s = json.load(f)
                self.open_trades              = s.get("open_trades", {})
                self.trade_history            = s.get("trade_history", [])
                self.main_balance             = s.get("main_balance", STARTING_CAPITAL)
                self.profit_pool              = s.get("profit_pool", 0.0)
                self.daily_pnl                = s.get("daily_pnl", 0.0)
                self.total_profit             = s.get("total_profit", 0.0)
                self.total_loss               = s.get("total_loss", 0.0)
                self.total_trades             = s.get("total_trades", 0)
                self.bot_paused               = s.get("bot_paused", False)
                self.available_for_withdrawal = s.get("available_for_withdrawal", 0.0)
                logger.info("State loaded.")
                return
            except Exception as e:
                logger.error(f"State load error: {e}")
        self._reset()

    def _reset(self):
        self.open_trades = {}; self.trade_history = []
        self.main_balance = STARTING_CAPITAL; self.profit_pool = 0.0
        self.daily_pnl = 0.0; self.total_profit = 0.0; self.total_loss = 0.0
        self.total_trades = 0; self.bot_paused = False
        self.available_for_withdrawal = 0.0

    def save(self):
        data = {
            "open_trades":              self.open_trades,
            "trade_history":            self.trade_history[-200:],
            "main_balance":             self.main_balance,
            "profit_pool":              self.profit_pool,
            "daily_pnl":               self.daily_pnl,
            "total_profit":             self.total_profit,
            "total_loss":              self.total_loss,
            "total_trades":             self.total_trades,
            "bot_paused":               self.bot_paused,
            "available_for_withdrawal": self.available_for_withdrawal,
            "saved_at":                 datetime.now().isoformat()
        }
        with open(STATE_FILE, "w") as f:
            json.dump(data, f, indent=2)

    @property
    def total_capital(self) -> float:
        return self.main_balance + self.profit_pool

    def can_trade(self, symbol: str, strength: float) -> tuple:
        if self.bot_paused:          return False, "Bot paused"
        if strength < 0.80:          return False, f"Signal weak ({strength*100:.0f}%)"
        if len(self.open_trades) >= MAX_OPEN_TRADES: return False, "Max 5 trades open"
        if symbol in self.open_trades: return False, f"Already holding {symbol}"
        return True, "OK"

    def calc_position(self, entry: float, profit_target: float, mult: float = 1.0) -> dict:
        risk      = self.total_capital * RISK_PER_TRADE * max(0.1, min(2.0, mult))
        sl        = round(entry * (1 - STOP_LOSS_PCT), 4)
        tp        = round(entry * (1 + profit_target), 4)
        dist      = entry - sl
        shares    = int(risk / dist) if dist > 0 else 0
        return {"shares":shares,"risk":round(risk,2),"stop_loss":sl,
                "take_profit":tp,"position_value":round(shares*entry,2)}

    def open_trade(self, signal: dict) -> bool:
        sym    = signal["symbol"]
        entry  = signal["current_price"]
        mult   = signal.get("position_mult", NEWS_SIZE_NORMAL)
        can, why = self.can_trade(sym, signal["strength"])
        if not can:
            logger.info(f"Trade rejected {sym}: {why}")
            return False
        pos = self.calc_position(entry, signal["profit_target"], mult)
        if pos["shares"] < 1:
            logger.warning(f"{sym}: <1 share, skip")
            return False

        self.open_trades[sym] = {
            "symbol":sym,"entry_price":entry,"shares":pos["shares"],
            "stop_loss":pos["stop_loss"],"take_profit":pos["take_profit"],
            "signal_strength":signal["strength"],"strategy":signal["strategy"],
            "entry_time":datetime.now().isoformat(),"reason":signal["reason"],
            "risk_amount":pos["risk"],"position_mult":mult,
            "news_score":signal.get("news_score",0),
            "news_decision":signal.get("news_decision",""),
            "profit_target_pct":signal["profit_target"]*100
        }
        self.total_trades += 1
        self.save()

        size_label = {1.5:"🔥 Strong (1.5x — great news)",
                      1.0:"✅ Normal (1.0x)",
                      0.5:"🔹 Small (0.5x — mixed news)"}.get(mult,f"{mult}x")
        strat = {"RSI_OVERSOLD":"📉 RSI Oversold","SMA_CROSSOVER":"📈 SMA Crossover"}.get(signal["strategy"],signal["strategy"])
        heads = "\n".join(signal.get("news_headlines",[])[:3])

        send_telegram(
            f"🟢 *TRADE OPENED: {sym}*\n\n"
            f"📋 Strategy:    `{strat}`\n"
            f"📥 Entry:       `${entry:.2f}`\n"
            f"🛑 Stop Loss:   `${pos['stop_loss']:.4f}` (-0.10%)\n"
            f"🎯 Take Profit: `${pos['take_profit']:.4f}` (+{signal['profit_target']*100:.1f}%)\n"
            f"📦 Shares:      `{pos['shares']}`\n"
            f"💵 Value:       `${pos['position_value']:.2f}`\n"
            f"⚠️  Risk:        `${pos['risk']:.2f}` (0.25%)\n"
            f"📊 Signal:      `{signal['strength']*100:.1f}%` ({signal['reason']})\n"
            f"📰 News:        `{signal.get('news_score',0):+d}` — {signal.get('news_decision','')}\n"
            f"📦 Size:        {size_label}\n"
            f"💼 Capital:     `${self.total_capital:.2f}`\n\n"
            f"*Headlines:*\n{heads}\n\n"
            f"⚡ *Execute BUY on eToro now!*", "BUY"
        )
        logger.info(f"Trade opened: {sym} @ ${entry} mult={mult}x")
        return True

    def close_trade(self, symbol: str, exit_price: float, exit_reason: str):
        if symbol not in self.open_trades: return
        t      = self.open_trades[symbol]
        pnl    = (exit_price - t["entry_price"]) * t["shares"]
        pnl_pct= ((exit_price - t["entry_price"]) / t["entry_price"]) * 100

        self.trade_history.append({
            "symbol":symbol,"entry":t["entry_price"],"exit":exit_price,
            "shares":t["shares"],"pnl":round(pnl,2),"pnl_pct":round(pnl_pct,2),
            "reason":exit_reason,"strategy":t["strategy"],
            "news_score":t.get("news_score",0),"pos_mult":t.get("position_mult",1.0),
            "timestamp":datetime.now().isoformat()
        })
        self.daily_pnl += pnl

        if pnl > 0:
            self.total_profit             += pnl
            self.profit_pool              += pnl * REINVEST_PROFIT_RATIO
            self.available_for_withdrawal += pnl * WITHDRAW_RATIO
        else:
            self.total_loss += abs(pnl)
            if self.profit_pool >= abs(pnl):
                self.profit_pool += pnl
            else:
                self.main_balance -= abs(pnl) - self.profit_pool
                self.profit_pool   = 0.0

        del self.open_trades[symbol]
        self.save()
        net = self.total_profit - self.total_loss
        compound_info = (f"\n💹 Reinvested: `${pnl*REINVEST_PROFIT_RATIO:.2f}` (80%)\n"
                        f"💵 Withdrawable: `${self.available_for_withdrawal:.2f}`") if pnl > 0 \
                       else "\n🛡 Loss absorbed by profit pool first"

        send_telegram(
            f"{'💰' if pnl>=0 else '📉'} *{'Take Profit' if exit_reason=='TAKE PROFIT' else 'Stop Loss'}: {symbol}*\n\n"
            f"📤 Exit:    `${exit_price:.2f}`\n"
            f"📥 Entry:   `${t['entry_price']:.2f}`\n"
            f"📦 Shares:  `{t['shares']}`\n"
            f"📊 Result:  `{'+'if pnl>=0 else ''}{pnl:.2f}$ ({pnl_pct:+.2f}%)`\n"
            f"📋 Reason:  `{exit_reason}`"
            f"{compound_info}\n\n"
            f"{'─'*26}\n"
            f"💼 Capital: `${self.total_capital:.2f}`\n"
            f"📊 Net P&L: `{net:+.2f}$`\n"
            f"🔢 Trades:  `{self.total_trades}`\n\n"
            f"⚡ *Close this trade on eToro now!*",
            "PROFIT" if pnl >= 0 else "LOSS"
        )
        logger.info(f"Trade closed: {symbol} {exit_reason} PnL=${pnl:.2f}")

    def monitor_trades(self):
        for symbol in list(self.open_trades.keys()):
            t = self.open_trades.get(symbol)
            if not t: continue
            try:
                import yfinance as yf
                df = yf.download(symbol, period="5d", interval="1d",
                                 progress=False, auto_adjust=True)
                if df is None or len(df) == 0: continue
                price = float(df["Close"].iloc[-1])
            except Exception as e:
                logger.error(f"Price {symbol}: {e}")
                continue

            pct = (price - t["entry_price"]) / t["entry_price"] * 100
            if price >= t["take_profit"]:
                self.close_trade(symbol, price, "TAKE PROFIT")
            elif price <= t["stop_loss"]:
                self.close_trade(symbol, price, "STOP LOSS")
            else:
                logger.info(f"  {symbol}: ${price:.2f} ({pct:+.2f}%) | SL=${t['stop_loss']:.4f} TP=${t['take_profit']:.4f}")

    def day_end_report(self):
        net = self.total_profit - self.total_loss
        send_telegram(
            f"📊 *Day-End Report*\n\n"
            f"💼 Capital:     `${self.total_capital:.2f}`\n"
            f"📅 Today P&L:   `{self.daily_pnl:+.2f}$`\n"
            f"💹 Profit Pool: `${self.profit_pool:.2f}`\n"
            f"💵 Withdraw:    `${self.available_for_withdrawal:.2f}`\n\n"
            f"📋 All-Time:\n"
            f"  ✅ Profit: `+${self.total_profit:.2f}`\n"
            f"  ❌ Loss:   `-${self.total_loss:.2f}`\n"
            f"  📊 Net:    `{net:+.2f}$`\n"
            f"  🔢 Trades: `{self.total_trades}`", "REPORT"
        )
        self.daily_pnl = 0.0
        self.save()

    def status_summary(self, prices: dict = None) -> str:
        net = self.total_profit - self.total_loss
        trades_text = ""
        for sym, t in self.open_trades.items():
            price = (prices or {}).get(sym, t["entry_price"])
            pct   = (price - t["entry_price"]) / t["entry_price"] * 100
            trades_text += (
                f"  {'🟢'if pct>=0 else '🔴'} *{sym}*: `${price:.2f}` ({pct:+.2f}%)\n"
                f"     SL:`${t['stop_loss']:.4f}` TP:`${t['take_profit']:.4f}` "
                f"News:`{t.get('news_score',0):+d}` Size:`{t.get('position_mult',1)}x`\n"
            )
        hist_text = ""
        for h in reversed(self.trade_history[-5:]):
            hist_text += f"  {'✅'if h['pnl']>=0 else '❌'} *{h['symbol']}*: `{h['pnl']:+.2f}$` ({h['pnl_pct']:+.2f}%) {h['reason']}\n"

        return (
            f"💼 *eToro Bot Status*\n\n"
            f"💰 Capital:     `${self.total_capital:.2f}`\n"
            f"💹 Profit Pool: `${self.profit_pool:.2f}`\n"
            f"📈 Profit:      `+${self.total_profit:.2f}`\n"
            f"📉 Loss:        `-${self.total_loss:.2f}`\n"
            f"📊 Net P&L:     `{net:+.2f}$`\n"
            f"💵 Withdraw:    `${self.available_for_withdrawal:.2f}`\n"
            f"🔢 Trades:      `{self.total_trades}`\n"
            f"⏸ Paused:      `{'Yes ⛔'if self.bot_paused else 'No ✅'}`\n\n"
            f"📂 *Open ({len(self.open_trades)}/5):*\n{trades_text or '  None\n'}\n"
            f"📋 *Last 5:*\n{hist_text or '  None\n'}"
        )
