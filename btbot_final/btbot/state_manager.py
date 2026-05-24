# state_manager.py — Persistent state (survives restarts)
import json, os, math
from datetime import datetime
from logger import log
import config


class StateManager:
    def __init__(self):
        self.open_trades   = {}
        self.trade_history = []
        self.balance       = config.STARTING_BALANCE
        self.total_pnl     = 0.0
        self.day_pnl       = 0.0
        self.wins          = 0
        self.losses        = 0

    def save(self):
        try:
            with open(config.STATE_FILE, "w") as f:
                json.dump({
                    "open_trades":   self.open_trades,
                    "trade_history": self.trade_history[-50:],
                    "balance":       round(self.balance, 6),
                    "total_pnl":     round(self.total_pnl, 6),
                    "day_pnl":       round(self.day_pnl, 6),
                    "wins":          self.wins,
                    "losses":        self.losses,
                    "saved_at":      datetime.now().isoformat(),
                }, f, indent=2, default=str)
        except Exception as e:
            log.error(f"[STATE] Save error: {e}")

    def load(self):
        if not os.path.exists(config.STATE_FILE):
            log.info("[STATE] Fresh start.")
            return
        try:
            with open(config.STATE_FILE) as f:
                d = json.load(f)
            self.open_trades   = d.get("open_trades", {})
            self.trade_history = d.get("trade_history", [])
            self.balance       = d.get("balance", config.STARTING_BALANCE)
            self.total_pnl     = d.get("total_pnl", 0.0)
            self.day_pnl       = d.get("day_pnl", 0.0)
            self.wins          = d.get("wins", 0)
            self.losses        = d.get("losses", 0)
            log.info(f"[STATE] Loaded | {len(self.open_trades)} open | "
                     f"balance=${self.balance:.2f} | pnl=${self.total_pnl:.4f}")
        except Exception as e:
            log.error(f"[STATE] Load error: {e}")

    def add_trade(self, symbol: str, trade: dict):
        self.open_trades[symbol] = trade
        self.save()

    def close_trade(self, symbol: str, exit_price: float, reason: str) -> dict:
        if symbol not in self.open_trades:
            return {}
        t        = self.open_trades.pop(symbol)
        entry    = t["entry_price"]
        qty      = t["qty"]
        pnl_usdt = round((exit_price - entry) * qty, 6)
        pnl_pct  = round(((exit_price - entry) / entry) * 100, 4)

        # Update balance
        self.balance   += pnl_usdt
        self.total_pnl += pnl_usdt
        self.day_pnl   += pnl_usdt
        if pnl_usdt > 0: self.wins   += 1
        else:             self.losses += 1

        closed = {**t, "exit_price": exit_price, "exit_reason": reason,
                  "pnl_usdt": pnl_usdt, "pnl_pct": pnl_pct,
                  "exit_time": datetime.now().isoformat()}
        self.trade_history.append(closed)
        self.save()
        return closed

    def position_size(self, price: float) -> float:
        risk_amt  = self.balance * config.RISK_PER_TRADE
        sl_price  = price * (1 - config.STOP_LOSS_PCT)
        risk_unit = price - sl_price
        if risk_unit <= 0: return 0.0
        qty = risk_amt / risk_unit
        return math.floor(qty * 100000) / 100000

    @property
    def total_trades(self): return self.wins + self.losses

    @property
    def win_rate(self):
        return f"{self.wins/self.total_trades*100:.1f}%" if self.total_trades else "0%"

    def stats(self):
        return {"balance": f"${self.balance:.2f}",
                "total_pnl": f"${self.total_pnl:+.4f}",
                "day_pnl":   f"${self.day_pnl:+.4f}",
                "trades":    self.total_trades,
                "wins":      self.wins, "losses": self.losses,
                "win_rate":  self.win_rate,
                "open":      len(self.open_trades)}
