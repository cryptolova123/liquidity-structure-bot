from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from liqbot.backtest.engine import run_backtest
from liqbot.config import BotConfig
from liqbot.data.candles import load_candles
from liqbot.execution.paper import PaperBroker
from liqbot.report import format_scan
from liqbot.risk.manager import RiskManager
from liqbot.strategy.signals import evaluate
from liqbot.structure.catalog import CATALOG, catalog_summary
from liqbot.structure.context import build_context


def cmd_scan(cfg: BotConfig) -> int:
    df = load_candles(cfg.data_source, cfg.symbol, cfg.timeframe, cfg.lookback, cfg.csv_path)
    ctx = build_context(df, cfg)
    sig = evaluate(ctx, cfg)
    print(format_scan(ctx, sig))
    return 0


def cmd_paper(cfg: BotConfig) -> int:
    df = load_candles(cfg.data_source, cfg.symbol, cfg.timeframe, cfg.lookback, cfg.csv_path)
    ctx = build_context(df, cfg)
    sig = evaluate(ctx, cfg)
    print(format_scan(ctx, sig))
    if sig is None:
        print("paper: no trade")
        return 0
    risk = RiskManager(cfg, cfg.starting_equity)
    broker = PaperBroker(cfg, risk)
    sized = risk.size(sig)
    if sized is None:
        print("paper: blocked by risk")
        return 0
    trade = broker.submit(sized, len(df) - 1)
    print(json.dumps({"mode": "paper", "side": trade.side, "qty": trade.qty, "entry": trade.entry, "stop": trade.stop, "target": trade.target, "equity": risk.equity}, indent=2))
    print("paper: order booked (not sent to a live exchange)")
    return 0


def cmd_backtest(cfg: BotConfig) -> int:
    df = load_candles(cfg.data_source, cfg.symbol, cfg.timeframe, cfg.lookback, cfg.csv_path)
    result = run_backtest(df, cfg)
    print(json.dumps({"equity": result.equity, "pnl": result.pnl, "trades": result.trades, "wins": result.wins, "losses": result.losses, "win_rate": result.win_rate, "max_drawdown": result.max_drawdown}, indent=2))
    return 0


def cmd_catalog() -> int:
    summary = catalog_summary()
    print(f"91 structures | {summary}")
    for row in CATALOG:
        print(f"{row['id']:02d}  {row['impl']:<10} {row['family']:<12} {row['name']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Liquidity structure paper bot")
    p.add_argument("command", choices=["scan", "paper", "backtest", "catalog"])
    p.add_argument("--config", default=None)
    p.add_argument("--source", default=None)
    p.add_argument("--symbol", default=None)
    p.add_argument("--timeframe", default=None)
    args = p.parse_args(argv)
    cfg = BotConfig.load(args.config)
    if args.source:
        cfg.data_source = args.source
    if args.symbol:
        cfg.symbol = args.symbol
    if args.timeframe:
        cfg.timeframe = args.timeframe
    if args.command == "scan":
        return cmd_scan(cfg)
    if args.command == "paper":
        return cmd_paper(cfg)
    if args.command == "backtest":
        return cmd_backtest(cfg)
    return cmd_catalog()


if __name__ == "__main__":
    raise SystemExit(main())
