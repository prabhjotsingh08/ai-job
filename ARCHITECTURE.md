# Architecture — how `game-job` works

This doc explains the project **folder by folder, file by file**, and how the pieces
**orchestrate** to deliver remote Unity job alerts. (See `README.md` for setup/usage.)

---

## Top-level layout

```
game-job/
├── main.py                  # entry point — orchestrates one full run
├── config.yaml              # tunables: keywords, exclude, remote_only, studios, countries
├── requirements.txt         # Python deps (requests, PyYAML, feedparser)
├── seen.json                # dedup state — jobs already alerted (committed back each run)
├── source_state.json        # per-source last-run timestamps (rate-limit throttling)
├── .env.example             # template of env/secret names (real .env is gitignored)
├── .gitignore               # excludes .env, venv, __pycache__
├── README.md                # setup + usage guide
├── ARCHITECTURE.md          # this file
├── .github/workflows/
│   └── job-alerts.yml        # GitHub Actions: schedule + run + commit state back
└── jobbot/                  # the package (all logic lives here)
    ├── job.py               # Job data model + dedup id
    ├── config.py            # loads config.yaml + reads secrets from env
    ├── filters.py           # keyword match + remote check
    ├── store.py             # SeenStore (seen.json)
    ├── schedule.py          # SourceState (source_state.json)
    ├── telegram.py          # notifier: Telegram
    ├── whatsapp.py          # notifier: WhatsApp (CallMeBot)
    ├── discord.py           # notifier: Discord webhook
    └── sources/             # one module per job source
        ├── __init__.py      # registry + collect_all() orchestrator
        ├── _http.py         # shared get_json / post_json helpers
        ├── remoteok.py, weworkremotely.py, arbeitnow.py, jobicy.py,
        ├── remotive.py, himalayas.py, hackernews.py,    # generic boards
        ├── adzuna.py, jooble.py,                        # aggregators (key-gated)
        └── greenhouse.py, lever.py, ashby.py            # studio boards (per-token)
```

---

## The data model — `jobbot/job.py`

Everything flows as a list of `Job` dataclasses. Every source converts its raw API/RSS
response into `Job` objects, so the rest of the pipeline is source-agnostic.

- Fields: `title, company, url, source, location, tags, description`.
- `uid` — sha1 of normalized `title + company`. This is the **dedup key**: studios that
  post the same role per-location collapse to one alert.
- `match_text()` — lowercased `title + company + tags` used for keyword matching
  (deliberately excludes description to avoid false positives like "we value unity").

## Config + secrets — `jobbot/config.py` + `config.yaml`

- `config.yaml` holds **what you tune**: `keywords`, `exclude`, `remote_only`,
  `studios` (greenhouse/lever/ashby tokens), `adzuna_countries`, `seen_retention_days`.
- `config.py` loads that file into a `Config` object, and exposes **secrets from
  environment variables** (never from the file): Telegram/WhatsApp/Discord creds and
  Adzuna/Jooble keys, plus `*_enabled` flags so a channel/source only runs when configured.

## Sources — `jobbot/sources/`

Each module exposes **`fetch(...) -> list[Job]`** and never raises (logs + returns `[]`
on error, so one bad source can't kill the run). Three families:

- **Generic boards** (`remoteok, weworkremotely, arbeitnow, jobicy, remotive, himalayas,
  hackernews`) — `fetch(cfg)`. Some declare `MIN_INTERVAL_HOURS` (Remotive 6, Himalayas 24)
  to self-throttle.
- **Aggregators** (`adzuna, jooble`) — `fetch(cfg)`, but **no-op unless their API key is
  set**. Throttled 6h/24h.
- **Studio boards** (`greenhouse, lever, ashby`) — `fetch(token)`, called once per token
  listed in `config.yaml`.
- `_http.py` — shared `get_json` / `post_json` with a common User-Agent.

`sources/__init__.py` is the **registry + orchestrator**: `collect_all(cfg, state)` runs
each generic source (skipping ones not yet "due" per `SourceState`), then each studio
token, and returns the combined `list[Job]`.

## Filtering — `jobbot/filters.py`

Two gates applied to every job:
- `matches(job, cfg)` — keyword include/exclude using **whole-word** regex (so "unity"
  doesn't match "comm·unity·"). Some sources also scan the body (`BODY_MATCH_SOURCES`:
  HN, Adzuna, Jooble); Remotive matches title-only (`TITLE_ONLY_SOURCES`) to dodge its
  kitchen-sink tags.
- `is_remote(job)` — remote-only boards always pass; others must contain a remote term
  (`remote/anywhere/distributed/wfh/worldwide/global`) in location/title (or body).

## State — `jobbot/store.py` + `jobbot/schedule.py`

- `SeenStore` (`seen.json`): map `uid -> timestamp`. `is_new()` gates alerts; `mark()`
  records sent jobs; `prune()` drops entries older than `seen_retention_days`.
- `SourceState` (`source_state.json`): map `source -> last-run timestamp`. `is_due(name,
  hours)` lets rate-limited sources skip runs. Both files are committed back by the
  workflow so state survives between runs.

## Notifiers — `jobbot/{telegram,whatsapp,discord}.py`

Each exposes `send_jobs(jobs, ...)` and formats a `Job` for that platform (Telegram HTML,
WhatsApp markup via CallMeBot, Discord embeds batched 10/message). `main.py` calls
whichever channels are enabled; if none are configured it errors out.

## Scheduler — `.github/workflows/job-alerts.yml`

Runs free on GitHub Actions: `schedule` (cron) + manual `workflow_dispatch`. Steps:
checkout → setup Python → `pip install` → run `python main.py` (secrets passed as env) →
commit `seen.json` + `source_state.json` back to the repo. (Note: GitHub throttles `*/15`
schedules; an external pinger hitting `workflow_dispatch` is the reliable alternative.)

---

## End-to-end orchestration (one run)

```
GitHub Actions (cron / dispatch)
        │
        ▼
   python main.py
        │
        ├─ load_config()            config.yaml + env secrets
        ├─ SeenStore(seen.json)     what we've already sent
        ├─ SourceState(...)         when each source last ran
        │
        ├─ collect_all(cfg, state)  ── sources/__init__.py
        │      ├─ generic sources  (skip if not "due"; mark when fetched)
        │      └─ studio tokens     greenhouse/lever/ashby
        │      → list[Job]          (~2000 raw listings)
        │
        ├─ for each Job:            ── filters.py
        │      matches() keyword?  ─ no → drop
        │      is_remote()?        ─ no → drop  (if remote_only)
        │      seen / dup?         ─ yes → drop
        │      → fresh[]            (only brand-new remote-Unity roles)
        │
        ├─ send fresh[] →           telegram / whatsapp / discord (enabled ones)
        │
        └─ mark seen + prune + save seen.json & source_state.json
                 │
                 ▼
   workflow commits state back → next run dedups correctly
```

**In one line:** *fetch everything → keep only new remote-Unity roles → push to your
channels → remember what was sent.* Steady state is silence; you get pinged only when a
genuinely new matching job appears.
