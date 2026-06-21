"""SeenStore: is_new/mark/prune and atomic save round-trip."""
import json
from datetime import datetime, timedelta, timezone

from jobbot.store import SeenStore


def test_mark_and_is_new(tmp_path):
    s = SeenStore(tmp_path / "seen.json")
    assert s.is_new("abc")
    s.mark("abc")
    assert not s.is_new("abc")


def test_save_roundtrip_valid_json(tmp_path):
    path = tmp_path / "seen.json"
    s = SeenStore(path)
    s.mark("abc")
    s.save()
    # File is valid JSON and reload sees the entry.
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "abc" in data
    assert not SeenStore(path).is_new("abc")
    # No leftover temp file.
    assert not (tmp_path / "seen.json.tmp").exists()


def test_prune_drops_old_keeps_recent(tmp_path):
    s = SeenStore(tmp_path / "seen.json")
    old = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    recent = datetime.now(timezone.utc).isoformat()
    s._data = {"old": old, "recent": recent}
    s.prune(retention_days=60)
    assert s.is_new("old")
    assert not s.is_new("recent")
