from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .swings import Swing


@dataclass(frozen=True)
class EqualLevel:
    kind: str  # EQH | EQL
    price: float
    members: tuple[Swing, ...]


@dataclass(frozen=True)
class LiquidityEvent:
    name: str
    side: str  # buy-side | sell-side
    level: float
    sweep_index: int
    swept_high: float | None
    swept_low: float | None
    notes: str


def detect_equal_levels(swings: list[Swing], atr_value: float, atr_mult: float) -> list[EqualLevel]:
    tol = max(atr_value * atr_mult, 1e-9)
    levels: list[EqualLevel] = []
    for kind, label in (("high", "EQH"), ("low", "EQL")):
        pts = [s for s in swings if s.kind == kind]
        used = set()
        for i, a in enumerate(pts):
            if i in used:
                continue
            cluster = [a]
            used.add(i)
            for j, b in enumerate(pts[i + 1 :], start=i + 1):
                if j in used:
                    continue
                if abs(b.price - a.price) <= tol:
                    cluster.append(b)
                    used.add(j)
            if len(cluster) >= 2:
                avg = sum(c.price for c in cluster) / len(cluster)
                levels.append(EqualLevel(label, avg, tuple(cluster)))
    return levels


def detect_sweeps(
    df: pd.DataFrame,
    swings: list[Swing],
    equals: list[EqualLevel],
    close_back: bool = True,
    lookback: int = 8,
) -> list[LiquidityEvent]:
    events: list[LiquidityEvent] = []
    if df.empty:
        return events
    i = len(df) - 1
    row = df.iloc[i]
    recent_highs = [s for s in swings if s.kind == "high" and s.index < i][-6:]
    recent_lows = [s for s in swings if s.kind == "low" and s.index < i][-6:]

    def _close_ok_short(level: float) -> bool:
        return (not close_back) or float(row["close"]) < level

    def _close_ok_long(level: float) -> bool:
        return (not close_back) or float(row["close"]) > level

    for eq in equals:
        last_member = max(eq.members, key=lambda s: s.index)
        if i - last_member.index > lookback + 3:
            continue
        if eq.kind == "EQH" and float(row["high"]) > eq.price and _close_ok_short(eq.price):
            events.append(
                LiquidityEvent(
                    name="liquidity_sweep_eqh",
                    side="buy-side",
                    level=eq.price,
                    sweep_index=i,
                    swept_high=float(row["high"]),
                    swept_low=None,
                    notes="Swept equal highs / buy-side liquidity",
                )
            )
        if eq.kind == "EQL" and float(row["low"]) < eq.price and _close_ok_long(eq.price):
            events.append(
                LiquidityEvent(
                    name="liquidity_sweep_eql",
                    side="sell-side",
                    level=eq.price,
                    sweep_index=i,
                    swept_high=None,
                    swept_low=float(row["low"]),
                    notes="Swept equal lows / sell-side liquidity",
                )
            )

    for sh in recent_highs:
        if i - sh.index > lookback:
            continue
        if float(row["high"]) > sh.price and _close_ok_short(sh.price):
            events.append(
                LiquidityEvent(
                    name="stop_hunt_high",
                    side="buy-side",
                    level=sh.price,
                    sweep_index=i,
                    swept_high=float(row["high"]),
                    swept_low=None,
                    notes="Stop hunt above swing high",
                )
            )
    for sl in recent_lows:
        if i - sl.index > lookback:
            continue
        if float(row["low"]) < sl.price and _close_ok_long(sl.price):
            events.append(
                LiquidityEvent(
                    name="stop_hunt_low",
                    side="sell-side",
                    level=sl.price,
                    sweep_index=i,
                    swept_high=None,
                    swept_low=float(row["low"]),
                    notes="Stop hunt below swing low",
                )
            )
    uniq: list[LiquidityEvent] = []
    seen = set()
    for ev in events:
        key = (ev.name, round(ev.level, 6), ev.side)
        if key not in seen:
            seen.add(key)
            uniq.append(ev)
    return uniq
