"""Ashby public posting API (per studio token).

https://api.ashbyhq.com/posting-api/job-board/<token>
"""
from __future__ import annotations

from ..job import Job
from ._http import get_json

TMPL = "https://api.ashbyhq.com/posting-api/job-board/{token}"


def fetch(token: str) -> list[Job]:
    data = get_json(TMPL.format(token=token))
    jobs: list[Job] = []
    for row in data.get("jobs", []):
        jobs.append(
            Job(
                title=row.get("title", ""),
                company=token,
                url=row.get("jobUrl", "") or row.get("applyUrl", ""),
                location=row.get("location", "") or "",
                tags=[row.get("department", ""), row.get("team", "")],
                description=row.get("descriptionPlain", "") or "",
                source=f"Ashby/{token}",
            )
        )
    return jobs
