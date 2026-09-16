# Project Ledger: liquidity-structure-bot

## Entry 2026-09-16 09:55 UTC

**What**: Initial project — paper-trading bot around the 91-structure institutional liquidity cheat sheet.
**When**: 2026-09-16 09:55 UTC
**Where**: Entire repo under `src/liqbot/`, `tests/test_core.py`, `config.example.yaml`, `README.md`
**How**: Primitive detectors (swings, EQH/EQL, sweeps, BOS/CHOCH/MSS, FVG, order blocks, sessions, PDH/PDL/PWH/PWL, premium/discount) plus a confluence scorer, paper broker, walk-forward backtest, and a 91-row catalog marked primitive/composed/visual.
**Why**: User asked for a trading bot that uses the information in https://x.com/alexmasoncrypto/status/2099925187714019711. Most of the 91 drawings are discretionary cartoons of the same liquidity story; the bot encodes the story rather than pretending each drawing is a separate edge.
**Verification**: `PYTHONPATH=src python3 -m pytest tests -q` → 7 passed. CLI `scan` and `backtest` on synthetic data completed. Backtest on planted synthetic series: 5 trades, 3 wins, equity 10191 from 10000.
**Commit**: GitHub main

---
