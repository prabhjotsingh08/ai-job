"""Remotive remote-jobs API, pre-filtered to AI Engineer roles.

https://remotive.com/api/remote-jobs?search=ai engineer
Remotive asks for <=4 calls/day, so this source runs on a 6h interval.
"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ._http import get_json

URL = "https://remotive.com/api/remote-jobs?search=ai%20engineer&limit=100"
MIN_INTERVAL_HOURS = 6


def fetch(cfg: Config) -> list[Job]:
    data = get_json(URL)
    jobs: list[Job] = []
    for row in data.get("jobs", []):
        jobs.append(
            Job(
                title=row.get("title", ""),
                company=row.get("company_name", ""),
                url=row.get("url", ""),
                location=row.get("candidate_required_location", "") or "Remote",
                tags=row.get("tags", []) or [],
                description=row.get("description", "") or "",
                source="Remotive",
            )
        )
    return jobs
