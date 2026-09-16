from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class FairValueGap:
    kind: str
    index: int
    top: float
    bottom: float
    filled: bool
    mid: float


def detect_fvgs(df: pd.DataFrame, min_size: float = 0.0) -> list[FairValueGap]:
    gaps: list[FairValueGap] = []
    if len(df) < 3:
        return gaps
    highs = df["high"].to_numpy()
    lows = df["low"].to_numpy()
    for i in range(2, len(df)):
        if lows[i] > highs[i - 2]:
            size = lows[i] - highs[i - 2]
            if size >= min_size:
                gaps.append(
                    FairValueGap(
                        "bullish",
                        i,
                        float(lows[i]),
                        float(highs[i - 2]),
                        False,
                        (float(lows[i]) + float(highs[i - 2])) / 2,
                    )
                )
        if highs[i] < lows[i - 2]:
            size = lows[i - 2] - highs[i]
            if size >= min_size:
                gaps.append(
                    FairValueGap(
                        "bearish",
                        i,
                        float(lows[i - 2]),
                        float(highs[i]),
                        False,
                        (float(lows[i - 2]) + float(highs[i])) / 2,
                    )
                )
    for g in gaps:
        later = df.iloc[g.index + 1 :]
        if g.kind == "bullish":
            g.filled = bool((later["low"] <= g.bottom).any())
        else:
            g.filled = bool((later["high"] >= g.top).any())
    return gaps


def active_fvgs(gaps: list[FairValueGap], kind: str | None = None) -> list[FairValueGap]:
    out = [g for g in gaps if not g.filled]
    if kind:
        out = [g for g in out if g.kind == kind]
    return out
