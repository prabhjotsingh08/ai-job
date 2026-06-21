"""Keyword matching for the AI-Engineer track, with whole-word boundaries.

A job is kept when its TITLE names an AI/ML-engineer role keyword AND at least one `topic`
(RAG/LLM/agent/agentic) appears in the title or description, AND it is not excluded by
seniority (title) or an experience requirement above `max_years` (description).

Substring matching is a trap ("ai" lives inside "*ai*rline"); we match each term only when
bounded by non-alphanumerics, which still allows phrases like "ai/ml engineer" and "gen ai".
"""
from __future__ import annotations

import re
from functools import lru_cache

from .config import Config
from .job import Job


@lru_cache(maxsize=512)
def _pattern(keyword: str) -> re.Pattern:
    # No alphanumeric immediately before/after the keyword.
    return re.compile(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])")


def _hit(terms: tuple[str, ...], text: str) -> bool:
    return any(_pattern(t).search(text) for t in terms)


# Years-of-experience patterns. Ranges ("7-10 years") are judged on their LOWER bound
# (minimum required); singletons ("6+ years", "minimum 7 years", "8 yrs") on their value.
_RANGE_YOE = re.compile(r"(\d{1,2})\s*(?:-|–|to)\s*\d{1,2}\s*\+?\s*(?:years|yrs|yoe)")
_SINGLE_YOE = re.compile(r"(\d{1,2})\s*\+?\s*(?:years|yrs|yoe)")


def _exceeds_years(text: str, max_years: int) -> bool:
    """True if the text states an experience requirement greater than max_years."""
    for m in _RANGE_YOE.finditer(text):
        if int(m.group(1)) > max_years:
            return True
    # Drop ranges first so a "7-10 years" upper bound isn't double-counted as a singleton.
    singles = _RANGE_YOE.sub(" ", text)
    for m in _SINGLE_YOE.finditer(singles):
        if int(m.group(1)) > max_years:
            return True
    return False


def matches(job: Job, cfg: Config) -> bool:
    """AI-Engineer match: role keyword in TITLE + >=1 topic in title/description, minus
    senior titles and JD experience requirements above cfg.max_years."""
    title = job.title.lower()
    body = title + " " + job.description.lower()
    if _hit(tuple(cfg.exclude), title):            # senior / lead / staff / ... in title
        return False
    if _exceeds_years(body, cfg.max_years):        # JD demands more than max_years
        return False
    if not _hit(tuple(cfg.keywords), title):       # title must name an AI/ML-engineer role
        return False
    return _hit(tuple(cfg.topics), body)           # >=1 topic (RAG/LLM/agent/agentic)


# Boards that ONLY list remote jobs — every result is remote by definition.
REMOTE_ONLY_SOURCES = {"RemoteOK", "WeWorkRemotely", "Jobicy", "Remotive", "Himalayas"}

# Sources whose body text is reliable signal (HN comments, aggregators queried per-term).
BODY_MATCH_SOURCES = {"HackerNews", "Adzuna", "Jooble"}

# Any of these (whole-word) in location/title (or body for body-match sources) marks remote.
REMOTE_TERMS = (
    "remote", "anywhere", "distributed", "wfh", "work from home", "work-from-home",
    "worldwide", "global", "fully remote", "remote-first",
)


def is_remote(job: Job) -> bool:
    """Remote-only boards always pass; other sources must contain a remote term in
    location/title (or body for body-match sources)."""
    if job.source in REMOTE_ONLY_SOURCES:
        return True
    text = f"{job.location} {job.title}".lower()
    if job.source in BODY_MATCH_SOURCES:
        text += " " + job.description.lower()
    return _hit(REMOTE_TERMS, text)
