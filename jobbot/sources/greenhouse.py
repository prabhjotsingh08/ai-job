"""Greenhouse job board API (per studio token).

https://boards-api.greenhouse.io/v1/boards/<token>/jobs?content=true
"""
from __future__ import annotations

import re

from ..job import Job
from ._http import get_json

TMPL = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
_TAGS = re.compile(r"<[^>]+>")


def fetch(token: str) -> list[Job]:
    data = get_json(TMPL.format(token=token))
    jobs: list[Job] = []
    for row in data.get("jobs", []):
        loc = (row.get("location") or {}).get("name", "")
        content = _TAGS.sub(" ", row.get("content", "") or "")
        jobs.append(
            Job(
                title=row.get("title", ""),
                company=token,
                url=row.get("absolute_url", ""),
                location=loc,
                description=content,
                source=f"Greenhouse/{token}",
            )
        )
    return jobs
