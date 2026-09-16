from __future__ import annotations

from dataclasses import dataclass, field

from liqbot.config import BotConfig
from liqbot.risk.manager import RiskManager, SizedOrder


@dataclass
class PaperTrade:
    side: str
    qty: float
    entry: float
    stop: float
    target: float
    open_index: int
    close_index: int | None = None
    exit: float | None = None
    pnl: float | None = None
    reason: str | None = None


@dataclass
class PaperBroker:
    cfg: BotConfig
    risk: RiskManager
    trades: list[PaperTrade] = field(default_factory=list)
    open_trade: PaperTrade | None = None

    def _costed_price(self, price: float, side: str, is_entry: bool) -> float:
        bps = (self.cfg.spread_bps + self.cfg.slippage_bps) / 10_000.0
        if side == "long":
            return price * (1 + bps) if is_entry else price * (1 - bps)
        return price * (1 - bps) if is_entry else price * (1 + bps)

    def submit(self, order: SizedOrder, index: int) -> PaperTrade | None:
        if self.open_trade is not None:
            return None
        fill = self._costed_price(order.entry, order.side, True)
        trade = PaperTrade(order.side, order.qty, fill, order.stop, order.target, index)
        self.open_trade = trade
        self.risk.on_open()
        return trade

    def mark(self, high: float, low: float, close: float, index: int) -> PaperTrade | None:
        t = self.open_trade
        if t is None:
            return None
        hit_stop = hit_tp = False
        if t.side == "long":
            hit_stop = low <= t.stop
            hit_tp = high >= t.target
        else:
            hit_stop = high >= t.stop
            hit_tp = low <= t.target
        if hit_stop and hit_tp:
            return self._close(t.stop, index, "stop_same_bar")
        if hit_stop:
            return self._close(t.stop, index, "stop")
        if hit_tp:
            return self._close(t.target, index, "target")
        return None

    def _close(self, price: float, index: int, reason: str) -> PaperTrade:
        t = self.open_trade
        assert t is not None
        exit_px = self._costed_price(price, t.side, False)
        pnl = (exit_px - t.entry) * t.qty if t.side == "long" else (t.entry - exit_px) * t.qty
        t.close_index = index
        t.exit = exit_px
        t.pnl = pnl
        t.reason = reason
        self.trades.append(t)
        self.open_trade = None
        self.risk.on_close(pnl)
        return t
