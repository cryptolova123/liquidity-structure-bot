from __future__ import annotations

from datetime import time

import pandas as pd

from liqbot.config import BotConfig


def _parse_hhmm(value: str) -> time:
    h, m = value.split(":")
    return time(int(h), int(m))


def annotate_sessions(df: pd.DataFrame, cfg: BotConfig) -> pd.DataFrame:
    out = df.copy()
    minutes = out["time"].dt.hour * 60 + out["time"].dt.minute
    out["session"] = "off"
    for name, window in cfg.sessions.items():
        start = _parse_hhmm(window.start)
        end = _parse_hhmm(window.end)
        s = start.hour * 60 + start.minute
        e = end.hour * 60 + end.minute
        if s <= e:
            mask = (minutes >= s) & (minutes < e)
        else:
            mask = (minutes >= s) | (minutes < e)
        out.loc[mask, "session"] = name
    out["day"] = out["time"].dt.floor("D")
    out["iso_week"] = out["time"].dt.isocalendar().week.astype(int)
    out["year"] = out["time"].dt.isocalendar().year.astype(int)
    return out


def session_extremes(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    if df.empty or "session" not in df.columns:
        return result
    last_day = df["day"].iloc[-1]
    today = df[df["day"] == last_day]
    for name, group in today.groupby("session"):
        if name == "off" or group.empty:
            continue
        result[name] = {
            "high": float(group["high"].max()),
            "low": float(group["low"].min()),
        }
    return result


def previous_day_levels(df: pd.DataFrame) -> dict[str, float | None]:
    days = df["day"].drop_duplicates().tolist()
    if len(days) < 2:
        return {"pdh": None, "pdl": None}
    prev = df[df["day"] == days[-2]]
    return {"pdh": float(prev["high"].max()), "pdl": float(prev["low"].min())}


def previous_week_levels(df: pd.DataFrame) -> dict[str, float | None]:
    keys = list(zip(df["year"], df["iso_week"]))
    uniq = []
    seen = set()
    for k in keys:
        if k not in seen:
            seen.add(k)
            uniq.append(k)
    if len(uniq) < 2:
        return {"pwh": None, "pwl": None}
    y, w = uniq[-2]
    prev = df[(df["year"] == y) & (df["iso_week"] == w)]
    return {"pwh": float(prev["high"].max()), "pwl": float(prev["low"].min())}
