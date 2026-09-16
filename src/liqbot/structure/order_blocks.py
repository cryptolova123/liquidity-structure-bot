from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .bos_choch import StructureEvent


@dataclass
class OrderBlock:
    kind: str
    index: int
    top: float
    bottom: float
    mitigated: bool
    name: str


def _last_opposite_candle(df: pd.DataFrame, before: int, want_bearish: bool) -> int | None:
    start = max(0, before - 12)
    for i in range(before - 1, start - 1, -1):
        o, c = float(df["open"].iloc[i]), float(df["close"].iloc[i])
        is_bear = c < o
        if want_bearish and is_bear:
            return i
        if not want_bearish and not is_bear:
            return i
    return None


def detect_order_blocks(df: pd.DataFrame, structure: list[StructureEvent], min_body: float = 0.0) -> list[OrderBlock]:
    blocks: list[OrderBlock] = []
    for ev in structure:
        if ev.name not in ("BOS", "CHOCH", "MSS"):
            continue
        want_bearish = ev.direction == "bullish"
        idx = _last_opposite_candle(df, ev.index, want_bearish=want_bearish)
        if idx is None:
            continue
        o, h, l, c = (float(df[col].iloc[idx]) for col in ("open", "high", "low", "close"))
        body = abs(c - o)
        if body < min_body:
            continue
        top, bottom = h, l
        later = df.iloc[idx + 1 :]
        if ev.direction == "bullish":
            mitigated = bool((later["low"] <= bottom).any())
            kind = "bullish"
        else:
            mitigated = bool((later["high"] >= top).any())
            kind = "bearish"
        name = "breaker" if ev.name in ("CHOCH", "MSS") else "order_block"
        blocks.append(OrderBlock(kind, idx, top, bottom, mitigated, name))
    return blocks


def active_blocks(blocks: list[OrderBlock], kind: str | None = None) -> list[OrderBlock]:
    out = [b for b in blocks if not b.mitigated]
    if kind:
        out = [b for b in out if b.kind == kind]
    return out
