"""Hacker News "Ask HN: Who is hiring?" monthly thread.

We find the most recent hiring thread via the Algolia HN API, then treat each
top-level comment as a job post and keyword-filter it downstream.
"""
from __future__ import annotations

import re

from ..config import Config
from ..job import Job
from ._http import get_json

SEARCH = (
    "https://hn.algolia.com/api/v1/search_by_date"
    "?query=%22Ask%20HN%3A%20Who%20is%20hiring%22&tags=story&hitsPerPage=5"
)
ITEM = "https://hn.algolia.com/api/v1/items/{id}"
_TAGS = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return _TAGS.sub(" ", text or "").replace("&#x2F;", "/").replace("&amp;", "&")


def fetch(cfg: Config) -> list[Job]:
    hits = get_json(SEARCH).get("hits", [])
    thread = next(
        (h for h in hits if "who is hiring" in (h.get("title", "").lower())),
        None,
    )
    if not thread:
        return []

    thread_id = thread.get("objectID")
    item = get_json(ITEM.format(id=thread_id))
    jobs: list[Job] = []
    for c in item.get("children", []):
        text = _clean(c.get("text", ""))
        if not text:
            continue
        # First line is usually "Company | Role | Location | ..."
        first_line = text.strip().splitlines()[0][:120]
        jobs.append(
            Job(
                title=first_line,
                company="(HN Who-is-hiring)",
                url=f"https://news.ycombinator.com/item?id={c.get('id')}",
                description=text,
                source="HackerNews",
            )
        )
    return jobs
