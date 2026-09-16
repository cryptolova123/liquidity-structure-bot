from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests


INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "1w": 604_800_000,
}


def _to_frame(rows: list[list]) -> pd.DataFrame:
    df = pd.DataFrame(
        rows,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore",
        ],
    )
    df["time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    for col in ("open", "high", "low", "close", "volume"):
        df[col] = df[col].astype(float)
    return df[["time", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def fetch_binance(symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": timeframe, "limit": min(limit, 1000)}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return _to_frame(r.json())


def load_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "time" not in df.columns:
        raise ValueError("CSV must include a time column")
    df["time"] = pd.to_datetime(df["time"], utc=True)
    for col in ("open", "high", "low", "close"):
        df[col] = df[col].astype(float)
    if "volume" not in df.columns:
        df["volume"] = 0.0
    return df[["time", "open", "high", "low", "close", "volume"]].reset_index(drop=True)


def synthetic_ohlcv(n: int = 400, seed: int = 7) -> pd.DataFrame:
    """Deterministic series with sweeps, FVGs, and a structure shift for tests/demos."""
    rng = np.random.default_rng(seed)
    t0 = pd.Timestamp("2026-01-01", tz="UTC")
    times = pd.date_range(t0, periods=n, freq="h")
    price = 100.0
    opens, highs, lows, closes = [], [], [], []
    for i in range(n):
        if i < 80:
            drift = 0.12
        elif i < 120:
            drift = 0.02
        elif i < 160:
            drift = -0.25
        elif i < 220:
            drift = -0.04
        elif i < 260:
            drift = 0.18
        else:
            drift = 0.05
        o = price
        noise = float(rng.normal(0, 0.35))
        c = max(1.0, o + drift + noise)
        h = max(o, c) + abs(float(rng.normal(0.25, 0.12)))
        l = min(o, c) - abs(float(rng.normal(0.25, 0.12)))
        if 100 <= i <= 108:
            h = 112.4 + (0.04 if i % 2 == 0 else 0.0)
            c = 111.6
        if i == 112:
            h = 113.6
            c = 110.8
            l = 110.2
        if 200 <= i <= 206:
            l = 88.1 - (0.03 if i % 2 == 0 else 0.0)
            c = 88.9
        if i == 210:
            l = 86.9
            c = 89.4
            h = 90.1
        opens.append(o)
        highs.append(h)
        lows.append(l)
        closes.append(c)
        price = c
    vol = rng.uniform(10, 40, size=n)
    return pd.DataFrame(
        {
            "time": times,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": vol,
        }
    )


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat(
        [
            df["high"] - df["low"],
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return tr.rolling(period, min_periods=1).mean()


def load_candles(source: str, symbol: str, timeframe: str, lookback: int, csv_path: str) -> pd.DataFrame:
    if source == "csv":
        df = load_csv(csv_path)
    elif source == "synthetic":
        df = synthetic_ohlcv(max(lookback, 300))
    else:
        try:
            df = fetch_binance(symbol, timeframe, lookback)
        except Exception:
            df = synthetic_ohlcv(max(lookback, 300))
    df = df.tail(lookback).reset_index(drop=True)
    df["atr"] = atr(df)
    return df


@dataclass
class CandleStore:
    df: pd.DataFrame

    @property
    def last(self) -> pd.Series:
        return self.df.iloc[-1]
