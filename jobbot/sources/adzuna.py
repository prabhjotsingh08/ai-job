"""Adzuna aggregator (covers Indeed-style listings). Free key: developer.adzuna.com.

No-op unless ADZUNA_APP_ID + ADZUNA_APP_KEY are set. Queried per country; remote/unity
signal lives in the body, so this source is in filters.BODY_MATCH_SOURCES.
"""
from __future__ import annotations

from urllib.parse import quote

from ..config import Config
from ..job import Job
from ._http import get_json

TMPL = (
    "https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    "?app_id={app_id}&app_key={app_key}&what={what}"
    "&results_per_page=50&content-type=application/json"
)
WHAT = quote("ai engineer")
MIN_INTERVAL_HOURS = 6


def fetch(cfg: Config) -> list[Job]:
    if not cfg.adzuna_enabled:
        return []
    jobs: list[Job] = []
    for country in cfg.adzuna_countries:
        url = TMPL.format(
            country=country, app_id=cfg.adzuna_app_id, app_key=cfg.adzuna_app_key, what=WHAT
        )
        data = get_json(url)
        for row in data.get("results", []):
            jobs.append(
                Job(
                    title=row.get("title", ""),
                    company=(row.get("company") or {}).get("display_name", ""),
                    url=row.get("redirect_url", ""),
                    location=(row.get("location") or {}).get("display_name", ""),
                    description=row.get("description", "") or "",
                    source="Adzuna",
                )
            )
    return jobs
