from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from liqbot.config import BotConfig
from liqbot.execution.paper import PaperBroker
from liqbot.risk.manager import RiskManager
from liqbot.strategy.signals import evaluate
from liqbot.structure.context import build_context


@dataclass
class BacktestResult:
    equity: float
    trades: int
    wins: int
    losses: int
    win_rate: float
    pnl: float
    max_drawdown: float


def run_backtest(df: pd.DataFrame, cfg: BotConfig, min_bars: int = 80) -> BacktestResult:
    risk = RiskManager(cfg, cfg.starting_equity)
    broker = PaperBroker(cfg, risk)
    peak = cfg.starting_equity
    max_dd = 0.0
    for i in range(min_bars, len(df)):
        window = df.iloc[: i + 1].reset_index(drop=True)
        if broker.open_trade is not None:
            row = window.iloc[-1]
            broker.mark(float(row["high"]), float(row["low"]), float(row["close"]), i)
        else:
            ctx = build_context(window, cfg)
            sig = evaluate(ctx, cfg)
            if sig is not None:
                sized = risk.size(sig)
                if sized is not None:
                    broker.submit(sized, i)
        peak = max(peak, risk.equity)
        max_dd = max(max_dd, peak - risk.equity)
    closed = broker.trades
    wins = sum(1 for t in closed if (t.pnl or 0) > 0)
    losses = sum(1 for t in closed if (t.pnl or 0) <= 0)
    pnl = risk.equity - cfg.starting_equity
    wr = (wins / len(closed)) if closed else 0.0
    return BacktestResult(risk.equity, len(closed), wins, losses, wr, pnl, max_dd)
