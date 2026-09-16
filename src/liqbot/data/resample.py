from __future__ import annotations

import pandas as pd

from .candles import atr

TF_TO_PANDAS = {
    "1m": "1min",
    "3m": "3min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "1h",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1D",
    "1w": "1W",
}


def timeframe_rank(tf: str) -> int:
    order = list(TF_TO_PANDAS)
    try:
        return order.index(tf)
    except ValueError:
        return 0


def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    rule = TF_TO_PANDAS.get(timeframe)
    if rule is None:
        return df.copy()
    work = df.copy()
    work = work.set_index(pd.DatetimeIndex(work["time"]))
    out = work.resample(rule, label="left", closed="left").agg(
        {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    out = out.dropna().reset_index()
    if "time" not in out.columns:
        out = out.rename(columns={"index": "time"})
    out["atr"] = atr(out)
    return out
