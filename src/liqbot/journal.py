from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PaperJournal:
    def __init__(self, path: str | Path = "state/paper_journal.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data: dict[str, Any] = {"equity": None, "trades": [], "scans": []}
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass

    def record_scan(self, payload: dict[str, Any]) -> None:
        row = {"ts": _now(), **payload}
        self.data.setdefault("scans", []).append(row)
        self.data["scans"] = self.data["scans"][-200:]
        self._flush()

    def record_trade(self, payload: dict[str, Any], equity: float) -> None:
        row = {"ts": _now(), **payload}
        self.data.setdefault("trades", []).append(row)
        self.data["equity"] = equity
        self._flush()

    def summary(self) -> dict[str, Any]:
        trades = self.data.get("trades") or []
        return {
            "path": str(self.path),
            "equity": self.data.get("equity"),
            "trades": len(trades),
            "last_trade": trades[-1] if trades else None,
            "scans": len(self.data.get("scans") or []),
        }

    def _flush(self) -> None:
        self.path.write_text(json.dumps(self.data, indent=2, default=str), encoding="utf-8")
