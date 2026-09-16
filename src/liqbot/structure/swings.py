from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Swing:
    index: int
    time: object
    price: float
    kind: str  # high | low


def detect_swings(df: pd.DataFrame, left: int = 2, right: int = 2) -> list[Swing]:
    swings: list[Swing] = []
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    n = len(df)
    for i in range(left, n - right):
        window_h = highs[i - left : i + right + 1]
        window_l = lows[i - left : i + right + 1]
        if highs[i] >= window_h.max() and (window_h == highs[i]).sum() == 1:
            swings.append(Swing(i, df["time"].iloc[i], float(highs[i]), "high"))
        if lows[i] <= window_l.min() and (window_l == lows[i]).sum() == 1:
            swings.append(Swing(i, df["time"].iloc[i], float(lows[i]), "low"))
    swings.sort(key=lambda s: s.index)
    return swings


def last_swings(swings: list[Swing], kind: str, count: int = 5) -> list[Swing]:
    subset = [s for s in swings if s.kind == kind]
    return subset[-count:]
