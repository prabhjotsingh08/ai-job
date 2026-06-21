"""Jooble aggregator. Free key: jooble.org/api/about.

No-op unless JOOBLE_API_KEY is set. Free quota is small, so this runs at most once
a day (MIN_INTERVAL_HOURS=24). Remote/unity signal lives in the body, so this source
is in filters.BODY_MATCH_SOURCES.
"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ._http import post_json

URL = "https://jooble.org/api/{key}"
MIN_INTERVAL_HOURS = 24


def fetch(cfg: Config) -> list[Job]:
    if not cfg.jooble_enabled:
        return []
    data = post_json(
        URL.format(key=cfg.jooble_key),
        {"keywords": "ai engineer", "location": "remote"},
    )
    jobs: list[Job] = []
    for row in data.get("jobs", []):
        jobs.append(
            Job(
                title=row.get("title", ""),
                company=row.get("company", ""),
                url=row.get("link", ""),
                location=row.get("location", ""),
                description=row.get("snippet", "") or "",
                source="Jooble",
            )
        )
    return jobs
