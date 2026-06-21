"""Arbeitnow public job board API: https://www.arbeitnow.com/api/job-board-api"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ._http import get_json

URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch(cfg: Config) -> list[Job]:
    data = get_json(URL)
    jobs: list[Job] = []
    for row in data.get("data", []):
        jobs.append(
            Job(
                title=row.get("title", ""),
                company=row.get("company_name", ""),
                url=row.get("url", ""),
                location=row.get("location", ""),
                tags=row.get("tags", []) or [],
                description=row.get("description", "") or "",
                source="Arbeitnow",
            )
        )
    return jobs
