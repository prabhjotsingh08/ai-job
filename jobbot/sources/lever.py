"""Lever postings API (per studio token).

https://api.lever.co/v0/postings/<token>?mode=json
"""
from __future__ import annotations

from ..job import Job
from ._http import get_json

TMPL = "https://api.lever.co/v0/postings/{token}?mode=json"


def fetch(token: str) -> list[Job]:
    data = get_json(TMPL.format(token=token))
    jobs: list[Job] = []
    for row in data:
        cats = row.get("categories", {}) or {}
        jobs.append(
            Job(
                title=row.get("text", ""),
                company=token,
                url=row.get("hostedUrl", "") or row.get("applyUrl", ""),
                location=cats.get("location", ""),
                tags=[cats.get("team", ""), cats.get("commitment", "")],
                description=row.get("descriptionPlain", "") or "",
                source=f"Lever/{token}",
            )
        )
    return jobs
