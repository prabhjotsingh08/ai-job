"""Himalayas remote-jobs API, pre-filtered to AI Engineer roles.

https://himalayas.app/jobs/api/search?q=ai engineer
Data is cached/refreshed every 24h and the API is rate-limited (429 if hammered),
so this source runs on a 24h interval.
"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ._http import get_json

URL = "https://himalayas.app/jobs/api/search?q=ai%20engineer"
MIN_INTERVAL_HOURS = 24


def fetch(cfg: Config) -> list[Job]:
    data = get_json(URL)
    jobs: list[Job] = []
    for row in data.get("jobs", []):
        locs = row.get("locationRestrictions") or []
        jobs.append(
            Job(
                title=row.get("title", ""),
                company=row.get("companyName", ""),
                url=row.get("applicationLink", "") or row.get("guid", ""),
                location=", ".join(locs) if isinstance(locs, list) else str(locs),
                description=row.get("description", "") or "",
                source="Himalayas",
            )
        )
    return jobs
