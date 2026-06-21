"""Persisted 'already-seen' store so we never alert the same job twice.

State is a JSON map {uid: iso-timestamp}. On GitHub Actions the workflow
commits this file back to the repo after each run.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import ROOT

SEEN_PATH = ROOT / "seen.json"


class SeenStore:
    def __init__(self, path: Path = SEEN_PATH):
        self.path = path
        self._data: dict[str, str] = {}
        if path.exists():
            try:
                self._data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def is_new(self, uid: str) -> bool:
        return uid not in self._data

    def mark(self, uid: str) -> None:
        self._data[uid] = datetime.now(timezone.utc).isoformat()

    def prune(self, retention_days: int) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        kept = {}
        for uid, ts in self._data.items():
            try:
                if datetime.fromisoformat(ts) >= cutoff:
                    kept[uid] = ts
            except ValueError:
                kept[uid] = ts  # keep unparseable entries rather than lose them
        self._data = kept

    def save(self) -> None:
        # Atomic write: a kill mid-write must not corrupt seen.json (a truncated file
        # would parse-fail on next load, reset to {}, and re-alert everything).
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self._data, indent=0, sort_keys=True), encoding="utf-8"
        )
        os.replace(tmp, self.path)
