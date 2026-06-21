"""Job sources. Each module exposes fetch(cfg) -> list[Job] and never raises;
on error it logs and returns []. collect_all() runs every enabled source that is
due (per its MIN_INTERVAL_HOURS and the SourceState).
"""
from __future__ import annotations

from ..config import Config
from ..job import Job
from ..schedule import SourceState
from . import (
    adzuna,
    arbeitnow,
    ashby,
    greenhouse,
    hackernews,
    himalayas,
    jobicy,
    jooble,
    lever,
    remoteok,
    remotive,
    weworkremotely,
)

# Generic boards always run; studio boards only run if configured.
# Order doesn't matter; rate-limited sources self-gate via MIN_INTERVAL_HOURS, and
# aggregators (adzuna/jooble) no-op until their API keys are set.
_GENERIC = [
    remoteok, weworkremotely, arbeitnow, jobicy, hackernews, remotive, himalayas,
    adzuna, jooble,
]


def collect_all(cfg: Config, state: SourceState) -> tuple[list[Job], list[str]]:
    """Return (jobs, errors). errors is one short string per source that failed (e.g. an
    exhausted aggregator key), so the caller can alert instead of failing silently."""
    jobs: list[Job] = []
    errors: list[str] = []
    for mod in _GENERIC:
        name = mod.__name__.split(".")[-1]
        interval = getattr(mod, "MIN_INTERVAL_HOURS", 0)
        if not state.is_due(name, interval):
            print(f"  [{name}] skipped (not due, every {interval}h)")
            continue
        try:
            found = mod.fetch(cfg)
            print(f"  [{name}] {len(found)} jobs")
            jobs.extend(found)
            state.mark(name)
        except Exception as e:  # a source must never kill the run
            print(f"  [{name}] ERROR: {e}")
            errors.append(f"{name}: {str(e)[:160]}")

    # Studio token failures are print-only: studio boards churn (a removed board 404s every
    # run) and would spam the alert. The alert focuses on generic boards + aggregators.
    for token in cfg.greenhouse:
        _run_studio(greenhouse, token, jobs)
    for token in cfg.lever:
        _run_studio(lever, token, jobs)
    for token in cfg.ashby:
        _run_studio(ashby, token, jobs)

    return jobs, errors


def _run_studio(mod, token: str, jobs: list[Job]) -> None:
    name = mod.__name__.split(".")[-1]
    try:
        found = mod.fetch(token)
        print(f"  [{name}:{token}] {len(found)} jobs")
        jobs.extend(found)
    except Exception as e:
        print(f"  [{name}:{token}] ERROR: {e}")
