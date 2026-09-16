# Liquidity Structure Bot

Paper-trading engine built around the *Institutional Price Action & Liquidity* cheat sheet (the 91-structure graphic from [@AlexMasonCrypto](https://x.com/alexmasoncrypto/status/2099925187714019711)).

This is **not** a magic insider feed. That image is a catalog of discretionary SMC/ICT-style cartoons. A bot cannot honestly “use all 91” as independent, stable signals — many are the same idea drawn 12 different ways, and several are unfalsifiable in hindsight.

What this repo *does* implement:

- The **primitives** those drawings actually rest on: swing points, equal highs/lows, liquidity sweeps / stop hunts, BOS / CHOCH / MSS, FVGs, order blocks / breakers, premium-discount, session levels, previous-day and previous-week highs/lows.
- **Composed** heuristics for traps, QML-like shapes, double/triple tops and bottoms, H&S-like structures.
- A **confluence scorer** that only fires when several primitives stack.
- **Paper execution** with spread, slippage, fixed-fraction risk, daily loss cap.
- A **walk-forward backtest** on the same rules.
- A numbered **catalog of all 91** names with implementation status: `primitive` / `composed` / `visual`.

It will **not** place live exchange orders. There is no API-key live broker on purpose.

## What the tweet is actually saying

The useful claim in that post is not “91 patterns.” It is:

1. Liquidity clusters at obvious swing highs/lows, session extremes, and equal levels.
2. Forced orders (stops, liquidations, breakout chases) sit there.
3. A trade idea is “who just got trapped, and where do they have to exit?” — not “this candle looks like #17.”

The bot scores that story: sweep → structure shift → discount/premium → FVG or order block.

## Quick start

```bash
python3 -m pip install -r requirements.txt
cp config.example.yaml config.yaml

# list the 91 structures and how they are treated
PYTHONPATH=src python3 -m liqbot.cli catalog

# run detectors on synthetic candles (offline)
PYTHONPATH=src python3 -m liqbot.cli scan --source synthetic

# same on Binance public klines (no API key)
PYTHONPATH=src python3 -m liqbot.cli scan --source binance --symbol BTCUSDT --timeframe 1h

# paper-book a hypothetical order if confluence prints
PYTHONPATH=src python3 -m liqbot.cli paper --source synthetic

# walk-forward backtest
PYTHONPATH=src python3 -m liqbot.cli backtest --source synthetic
```

Tests:

```bash
PYTHONPATH=src python3 -m pytest tests -q
```

## How a signal is built

Default rules (all toggleable in `config.yaml`):

1. Detect confirmed fractal swings.
2. Cluster them into EQH / EQL pools (width = `equal_level_atr_mult * ATR`).
3. A **sweep** is a wick through the pool that **closes back** through the level.
4. A **BOS** is a close through the latest opposite swing. First opposite BOS after a trend is **CHOCH / MSS**.
5. **FVG** = 3-candle imbalance. **Order block** = last opposite candle before the displacement that made BOS/CHOCH.
6. Price below the midpoint of recent swings is **discount** (longs preferred); above is **premium**.
7. Score the stack. Trade only if `score >= min_score` and risk rules pass.
8. Stop beyond the swept extreme; target = `rr_target` times that risk.

Visual-only rows in the catalog (Wyckoff schematics, Elliott labels, “Can-Can”, news grabs, etc.) are **not** traded by themselves. They are listed so you can see what was omitted and why.

## Honest limits

- Pattern names on that sheet overlap. Detecting “Flag A + Flag B” and “Compression Liquidity” as separate edges is how you curve-fit noise.
- No funding, OI, liquidation heatmaps, or footprint data yet. Those would be the next real increment if you want “where the forced orders are,” not more cartoons.
- Synthetic and short public-kline backtests are for plumbing, not a performance claim.
- Markets gap. Same-bar stop+target is assumed stop-first.

Not financial advice. You can lose the entire account.

## Project layout

```
src/liqbot/
  data/          candles, sessions, PDH/PDL
  structure/     swings, liquidity, BOS, FVG, OBs, catalog
  strategy/      confluence score
  risk/          sizing and daily cap
  execution/     paper broker
  backtest/      walk-forward engine
  cli.py
```
