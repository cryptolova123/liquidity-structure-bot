from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SessionWindow:
    start: str
    end: str


@dataclass
class BotConfig:
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    lookback: int = 500
    exchange: str = "binance"
    swing_left: int = 2
    swing_right: int = 2
    equal_level_atr_mult: float = 0.15
    sweep_close_back: bool = True
    fvg_min_atr_mult: float = 0.05
    ob_body_min_atr_mult: float = 0.05
    sessions: dict[str, SessionWindow] = field(
        default_factory=lambda: {
            "asia": SessionWindow("00:00", "08:00"),
            "london": SessionWindow("08:00", "13:00"),
            "newyork": SessionWindow("13:00", "21:00"),
        }
    )
    min_score: int = 3
    htf_timeframe: str = "4h"
    require_sweep: bool = True
    require_structure_shift: bool = True
    prefer_discount_for_longs: bool = True
    prefer_premium_for_shorts: bool = True
    risk_per_trade_pct: float = 0.5
    max_open_trades: int = 1
    max_daily_loss_pct: float = 2.0
    rr_target: float = 2.0
    spread_bps: float = 2.0
    slippage_bps: float = 3.0
    mode: str = "paper"
    starting_equity: float = 10_000.0
    data_source: str = "binance"
    csv_path: str = "examples/sample_ohlcv.csv"

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "BotConfig":
        sessions = {}
        for name, window in (raw.get("sessions") or {}).items():
            sessions[name] = SessionWindow(window["start"], window["end"])
        known = {f.name for f in cls.__dataclass_fields__.values()}
        kwargs = {k: v for k, v in raw.items() if k in known and k != "sessions"}
        cfg = cls(**kwargs)
        if sessions:
            cfg.sessions = sessions
        return cfg

    @classmethod
    def load(cls, path: str | Path | None = None) -> "BotConfig":
        if path is None:
            for candidate in ("config.yaml", "config.example.yaml"):
                if Path(candidate).exists():
                    path = candidate
                    break
        if path and Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return cls.from_dict(yaml.safe_load(f) or {})
        return cls()
