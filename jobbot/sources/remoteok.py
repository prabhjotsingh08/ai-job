"""RemoteOK public JSON API: https://remoteok.com/api

Fetches the generic feed plus one tag-filtered query per cfg.remoteok_tags (the API
supports ?tags=<tag>), merged and deduped. Broader tags only surface more candidate
rows; the strict-Unity keyword filter downstream is still the gate, so no extra noise.
"""
from __future__ import annotations

from urllib.parse import quote

from ..config import Config
from ..job import Job
from ._http import get_json

URL = "https://remoteok.com/api"
TAG_URL = "https://remoteok.com/api?tags={tag}"

# Generic feed + one query per tag = several requests; RemoteOK rate-limits hard
# (Cloudflare 429). Self-gate to every 3h so we don't get the IP blocked.
MIN_INTERVAL_HOURS = 3


def _rows_to_jobs(data, jobs: list[Job], seen: set[str]) -> None:
    # First element is a legal/metadata notice; skip non-dict / metadata rows.
    for row in data:
        if not isinstance(row, dict) or "position" not in row:
            continue
        job = Job(
            title=row.get("position", ""),
            company=row.get("company", ""),
            url=row.get("url", "") or row.get("apply_url", ""),
            location=row.get("location", "") or "Remote",
            tags=row.get("tags", []) or [],
            description=row.get("description", "") or "",
            source="RemoteOK",
        )
        if job.uid in seen:
            continue
        seen.add(job.uid)
        jobs.append(job)


def fetch(cfg: Config) -> list[Job]:
    jobs: list[Job] = []
    seen: set[str] = set()
    _rows_to_jobs(get_json(URL), jobs, seen)
    for tag in cfg.remoteok_tags:
        _rows_to_jobs(get_json(TAG_URL.format(tag=quote(str(tag)))), jobs, seen)
    return jobs
