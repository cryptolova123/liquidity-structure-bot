from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .swings import Swing


@dataclass(frozen=True)
class StructureEvent:
    name: str  # BOS | CHOCH | MSS
    direction: str  # bullish | bearish
    index: int
    level: float
    notes: str


def detect_market_structure(df: pd.DataFrame, swings: list[Swing]) -> tuple[str, list[StructureEvent]]:
    """Walk swings + closes to label trend and structure shifts."""
    events: list[StructureEvent] = []
    trend = "unknown"
    last_high: Swing | None = None
    last_low: Swing | None = None
    confirmed_high: Swing | None = None
    confirmed_low: Swing | None = None

    highs = [s for s in swings if s.kind == "high"]
    lows = [s for s in swings if s.kind == "low"]
    if not highs or not lows:
        return trend, events

    for i in range(len(df)):
        close = float(df["close"].iloc[i])
        formed_highs = [s for s in highs if s.index <= i]
        formed_lows = [s for s in lows if s.index <= i]
        if formed_highs:
            last_high = formed_highs[-1]
        if formed_lows:
            last_low = formed_lows[-1]

        if last_high and close > last_high.price and (not events or events[-1].level != last_high.price or events[-1].direction != "bullish"):
            name = "BOS"
            if trend == "bearish":
                name = "CHOCH"
            if trend in ("bearish", "unknown"):
                if trend == "bearish":
                    events.append(StructureEvent(name, "bullish", i, last_high.price, "Break of bearish structure"))
                else:
                    events.append(StructureEvent("BOS", "bullish", i, last_high.price, "Bullish break of structure"))
                trend = "bullish"
            elif trend == "bullish":
                events.append(StructureEvent("BOS", "bullish", i, last_high.price, "Continuation BOS"))
            confirmed_high = last_high

        if last_low and close < last_low.price and (not events or events[-1].level != last_low.price or events[-1].direction != "bearish"):
            if trend == "bullish":
                events.append(StructureEvent("CHOCH", "bearish", i, last_low.price, "Break of bullish structure"))
                trend = "bearish"
            elif trend == "unknown":
                events.append(StructureEvent("BOS", "bearish", i, last_low.price, "Bearish break of structure"))
                trend = "bearish"
            else:
                events.append(StructureEvent("BOS", "bearish", i, last_low.price, "Continuation BOS"))
            confirmed_low = last_low

    tagged: list[StructureEvent] = []
    for ev in events:
        if ev.name == "CHOCH":
            tagged.append(StructureEvent("CHOCH", ev.direction, ev.index, ev.level, ev.notes))
            tagged.append(StructureEvent("MSS", ev.direction, ev.index, ev.level, "Market structure shift"))
        else:
            tagged.append(ev)
    return trend, tagged


def latest_structure(events: list[StructureEvent], names: tuple[str, ...]) -> StructureEvent | None:
    for ev in reversed(events):
        if ev.name in names:
            return ev
    return None
