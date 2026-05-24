#!/usr/bin/env python3
# bot_engine.py — Core trading engine for btbot & ps1trade
import time, threading, os, sys
from datetime import datetime
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import telegram_notify as tg
from logger        import log
from strategy      import detect_signal
from market_filter import check_market
from state_manager import StateManager

try:
    from binance.client     import Client
    from binance.exceptions import BinanceAPIException
    _BINANCE_OK = True
except ImportError:
    _BINANCE_OK = False


class BotEngine:
    def __init__(self):
        self.is_live  = config.IS_LIVE
        self.client   = None
        self.state    = StateManager()
        self._running = False
        self._last_hr = datetime.now()
        log.info(f"[{config.BOT_NAME}] v{config.BOT_VERSION} | "
                 f"mode={'LIVE 🔴' if self.is_live else 'PAPER 📄'}")

    # ── Connect ───────────────────────────────────────────────────────
    def connect(self) -> bool:
        tg.test_ok()
        if not _BINANCE_OK:
            log.error("python-binance not installed!"); return False
        try:
            self.client = Client(
                config.BINANCE_API_KEY, config.BINANCE_SECRET_KEY,
                testnet=config.BINANCE_TESTNET
            )
            info = self.client.get_account()
            log.info(f"[BINANCE] Connected | canTrade={info['canTrade']}")
            return True
        except Exception as e:
            log.error(f"[BINANCE] Connect failed: {e}"); return False

    # ── Data ──────────────────────────────────────────────────────────
    def fetch(self, symbol: str) -> pd.DataFrame:
        try:
            klines = self.client.get_historical_klines(
                symbol, "15m", config.KLINE_LOOKBACK
            )
            df = pd.DataFrame(klines, columns=[
                'ts','open','high','low','close','volume',
                'cts','qv','trades','tb','tq','ign'
            ])
            for c in ['open','high','low','close','volume']:
                df[c] = df[c].astype(float)
            return df
        except Exception as e:
            log.error(f"[DATA] {symbol}: {e}"); return pd.DataFrame()

    def price(self, symbol: str) -> float:
        try:
            return float(self.client.get_symbol_ticker(symbol=symbol)['price'])
        except Exception as e:
            log.error(f"[PRICE] {symbol}: {e}"); return 0.0

    def balance(self) -> float:
        if not self.is_live:
            return self.state.balance
        try:
            return float(self.client.get_asset_balance(asset='USDT')['free'])
        except:
            return self.state.balance

    # ── Orders ────────────────────────────────────────────────────────
    def _buy(self, symbol: str, qty: float) -> bool:
        if not self.is_live:
            log.info(f"[PAPER] BUY {symbol} qty={qty}")
            return True
        try:
            self.client.order_market_buy(symbol=symbol, quantity=qty)
            return True
        except BinanceAPIException as e:
            log.error(f"[ORDER] Buy {symbol} failed: {e}"); return False

    def _sell(self, symbol: str, qty: float) -> bool:
        if not self.is_live:
            log.info(f"[PAPER] SELL {symbol} qty={qty}")
            return True
        try:
            self.client.order_market_sell(symbol=symbol, quantity=qty)
            return True
        except BinanceAPIException as e:
            log.error(f"[ORDER] Sell {symbol} failed: {e}"); return False

    # ── Open / Close ──────────────────────────────────────────────────
    def open_trade(self, symbol: str, sig: dict):
        entry = sig['price'] or self.price(symbol)
        qty   = self.state.position_size(entry)
        if qty <= 0:
            log.warning(f"[TRADE] {symbol} qty=0, skipping"); return

        tp = round(entry * (1 + sig['tp_pct']), 8)
        sl = round(entry * (1 - sig['sl_pct']), 8)

        if not self._buy(symbol, qty): return

        trade = {"symbol": symbol, "entry_price": entry, "qty": qty,
                 "take_profit": tp, "stop_loss": sl,
                 "tp_pct": sig['tp_pct'], "sl_pct": sig['sl_pct'],
                 "strategy": sig['strategy'], "strength": sig['strength'],
                 "reason": sig['reason'], "current": entry,
                 "time": datetime.now().isoformat()}
        self.state.add_trade(symbol, trade)

        log.info(f"[TRADE] OPENED {symbol} | entry={entry:.6f} | "
                 f"qty={qty} | tp={tp:.6f} | sl={sl:.6f} | {sig['strategy']}")
        tg.trade_opened(symbol, entry, qty, tp, sl,
                        sig['strategy'], sig['strength'], sig['reason'])

    def close_trade(self, symbol: str, price: float, reason: str):
        t = self.state.open_trades.get(symbol)
        if not t: return
        if not self._sell(symbol, t['qty']): return

        closed = self.state.close_trade(symbol, price, reason)
        pu, pp = closed.get('pnl_usdt', 0), closed.get('pnl_pct', 0)
        log.info(f"[TRADE] CLOSED {symbol} ({reason}) | exit={price:.6f} | "
                 f"pnl={pp:+.2f}% ${pu:+.4f}")
        if reason == "TAKE PROFIT": tg.trade_closed_tp(symbol, t['entry_price'], price, pu, pp)
        else:                        tg.trade_closed_sl(symbol, t['entry_price'], price, pu, pp)

    # ── Exit monitor (30s thread) ─────────────────────────────────────
    def _exit_loop(self):
        log.info("[EXIT] Monitor started (30s)")
        while self._running:
            for sym in list(self.state.open_trades):
                t = self.state.open_trades.get(sym)
                if not t: continue
                p = self.price(sym)
                if p <= 0: continue
                self.state.open_trades[sym]['current'] = p
                if p >= t['take_profit']:
                    self.close_trade(sym, p, "TAKE PROFIT")
                elif p <= t['stop_loss']:
                    self.close_trade(sym, p, "STOP LOSS")
            time.sleep(config.EXIT_CHECK_SEC)

    # ── Scan (2 min) ──────────────────────────────────────────────────
    def _scan(self):
        log.info(f"[SCAN] Scanning {len(config.SYMBOLS)} pairs | "
                 f"open={len(self.state.open_trades)}/{config.MAX_OPEN_TRADES}")
        found = 0
        for sym in config.SYMBOLS:
            if sym in self.state.open_trades: continue
            if len(self.state.open_trades) >= config.MAX_OPEN_TRADES: break

            df  = self.fetch(sym)
            if df.empty: continue

            mkt = check_market(df)
            if not mkt['tradeable']:
                log.debug(f"[SCAN] {sym} market skip | {mkt['score']} | {mkt['failing']}")
                continue

            sig = detect_signal(sym, df)
            if sig['signal']:
                log.info(f"[SCAN] {sym} SIGNAL {sig['strategy']} {sig['strength']:.0%}")
                self.open_trade(sym, sig)
                found += 1
                time.sleep(0.3)
            else:
                log.debug(f"[SCAN] {sym} no signal | RSI={sig['rsi']}")

        log.info(f"[SCAN] Done | {found} trades opened | "
                 f"balance=${self.state.balance:.2f}")

    # ── Hourly report ─────────────────────────────────────────────────
    def _check_hourly(self):
        if (datetime.now() - self._last_hr).seconds >= 3600:
            self._last_hr = datetime.now()
            tg.hourly(self.state.stats(), self.state.open_trades)

    # ── Start ─────────────────────────────────────────────────────────
    def start(self):
        self.state.load()
        if not self.connect():
            log.error("Cannot connect — aborting."); return

        self._running = True
        threading.Thread(target=self._exit_loop, daemon=True).start()
        tg.started(self.state.balance, config.BOT_MODE)
        log.info(f"[{config.BOT_NAME}] Running. "
                 f"Scan={config.SCAN_INTERVAL_SEC}s Exit={config.EXIT_CHECK_SEC}s")

        while self._running:
            try:
                self._scan()
                self._check_hourly()
                time.sleep(config.SCAN_INTERVAL_SEC)
            except KeyboardInterrupt:
                self._running = False
                tg.stopped("Manual stop")
            except Exception as e:
                import traceback
                self._running = False
                tg.error(f"{type(e).__name__}: {e}\n{traceback.format_exc()[:300]}")
                log.critical(f"FATAL: {e}")

        self.state.save()
        log.info(f"[{config.BOT_NAME}] Stopped. {self.state.stats()}")
