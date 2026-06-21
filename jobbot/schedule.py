"""Per-source poll-interval state so rate-limited sources aren't hit every run.

Backed by source_state.json {source_name: last-run iso-timestamp}, committed back
by the workflow like seen.json. Fast sources use interval 0 (always due).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import ROOT

STATE_PATH = ROOT / "source_state.json"


class SourceState:
    def __init__(self, path: Path = STATE_PATH):
        self.path = path
        self._data: dict[str, str] = {}
        if path.exists():
            try:
                self._data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def is_due(self, name: str, interval_hours: float) -> bool:
        if interval_hours <= 0:
            return True
        ts = self._data.get(name)
        if not ts:
            return True
        try:
            last = datetime.fromisoformat(ts)
        except ValueError:
            return True
        return datetime.now(timezone.utc) - last >= timedelta(hours=interval_hours)

    def mark(self, name: str) -> None:
        self._data[name] = datetime.now(timezone.utc).isoformat()

    def save(self) -> None:
        # Atomic write (see store.SeenStore.save) so an interrupted run can't corrupt
        # source_state.json.
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self._data, indent=0, sort_keys=True), encoding="utf-8"
        )
        os.replace(tmp, self.path)
