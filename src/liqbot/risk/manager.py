from __future__ import annotations

from dataclasses import dataclass

from liqbot.config import BotConfig
from liqbot.strategy.signals import Signal


@dataclass
class SizedOrder:
    side: str
    qty: float
    entry: float
    stop: float
    target: float
    risk_amount: float


class RiskManager:
    def __init__(self, cfg: BotConfig, equity: float):
        self.cfg = cfg
        self.equity = equity
        self.day_pnl = 0.0
        self.open_trades = 0

    def can_trade(self) -> tuple[bool, str]:
        if self.open_trades >= self.cfg.max_open_trades:
            return False, "max open trades"
        cap = self.equity * (self.cfg.max_daily_loss_pct / 100.0)
        if self.day_pnl <= -cap:
            return False, "max daily loss"
        return True, "ok"

    def size(self, signal: Signal) -> SizedOrder | None:
        ok, _ = self.can_trade()
        if not ok:
            return None
        risk_pct = self.cfg.risk_per_trade_pct / 100.0
        risk_amount = self.equity * risk_pct
        per_unit = abs(signal.entry - signal.stop)
        if per_unit <= 0:
            return None
        qty = risk_amount / per_unit
        return SizedOrder(signal.side, qty, signal.entry, signal.stop, signal.target, risk_amount)

    def on_close(self, pnl: float) -> None:
        self.equity += pnl
        self.day_pnl += pnl
        self.open_trades = max(0, self.open_trades - 1)

    def on_open(self) -> None:
        self.open_trades += 1
