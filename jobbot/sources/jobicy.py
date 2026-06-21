"""Jobicy remote jobs API: https://jobicy.com/api/v2/remote-jobs"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ._http import get_json

# Generic remote feed (count=100); the AI title+topic filter is the precision gate.
URL = "https://jobicy.com/api/v2/remote-jobs?count=100"


def fetch(cfg: Config) -> list[Job]:
    data = get_json(URL)
    jobs: list[Job] = []
    for row in data.get("jobs", []):
        jobs.append(
            Job(
                title=row.get("jobTitle", ""),
                company=row.get("companyName", ""),
                url=row.get("url", ""),
                location=row.get("jobGeo", "") or "Remote",
                tags=row.get("jobIndustry", []) or [],
                description=row.get("jobExcerpt", "") or "",
                source="Jobicy",
            )
        )
    return jobs
