"""Source parsers: raw API payload -> Job mapping (offline, get_json monkeypatched)."""
import types

from jobbot import sources
from jobbot.config import Config
from jobbot.schedule import SourceState
from jobbot.sources import greenhouse, hackernews, remoteok


def _cfg():
    return Config({})


def test_remoteok_parses_and_skips_metadata(monkeypatch):
    payload = [
        {"legal": "notice row, no position key"},
        {"position": "Unity Developer", "company": "Acme", "url": "https://x/1",
         "location": "", "tags": ["unity"], "description": "d"},
    ]
    monkeypatch.setattr(remoteok, "get_json", lambda url: payload)
    jobs = remoteok.fetch(_cfg())
    assert len(jobs) == 1
    j = jobs[0]
    assert j.title == "Unity Developer"
    assert j.company == "Acme"
    assert j.location == "Remote"  # empty location falls back to "Remote"
    assert j.source == "RemoteOK"


def test_remoteok_merges_and_dedups_tag_queries(monkeypatch):
    generic = [
        {"legal": "notice"},
        {"position": "Unity Developer", "company": "Acme", "url": "https://x/1"},
    ]
    tagged = [
        {"position": "Unity Developer", "company": "Acme", "url": "https://x/diff"},  # dup
        {"position": "Unity Engineer", "company": "Beta", "url": "https://x/2"},      # new
    ]

    def fake_get_json(url):
        return tagged if "tags=" in url else generic

    monkeypatch.setattr(remoteok, "get_json", fake_get_json)
    cfg = Config({"remoteok_tags": ["unity"]})
    jobs = remoteok.fetch(cfg)
    # Acme dup collapsed by uid; Beta added -> 2 unique.
    assert len(jobs) == 2
    titles = {j.title for j in jobs}
    assert titles == {"Unity Developer", "Unity Engineer"}


def test_greenhouse_strips_html_and_tags_company(monkeypatch):
    payload = {"jobs": [{
        "title": "Gameplay Engineer",
        "absolute_url": "https://boards/abc",
        "location": {"name": "Remote"},
        "content": "<p>Build <b>Unity</b> games</p>",
    }]}
    monkeypatch.setattr(greenhouse, "get_json", lambda url: payload)
    jobs = greenhouse.fetch("riotgames")
    assert len(jobs) == 1
    j = jobs[0]
    assert j.company == "riotgames"
    assert j.source == "Greenhouse/riotgames"
    assert "<" not in j.description and "Unity" in j.description


def test_collect_all_captures_generic_source_errors(monkeypatch):
    def boom(cfg):
        raise RuntimeError("403 quota exceeded")

    mod = types.SimpleNamespace(__name__="jobbot.sources.adzuna", fetch=boom)
    monkeypatch.setattr(sources, "_GENERIC", [mod])
    jobs, errors = sources.collect_all(Config({}), SourceState())
    assert jobs == []
    assert len(errors) == 1
    assert "adzuna" in errors[0] and "403 quota exceeded" in errors[0]


def test_hackernews_picks_thread_and_comments(monkeypatch):
    search = {"hits": [
        {"title": "Ask HN: Who is hiring? (June 2026)", "objectID": "111"},
        {"title": "something else", "objectID": "999"},
    ]}
    item = {"children": [
        {"id": 1, "text": "Acme | Unity Dev | Remote\nmore details"},
        {"id": 2, "text": ""},  # empty comment skipped
    ]}

    def fake_get_json(url):
        return item if "items/111" in url else search

    monkeypatch.setattr(hackernews, "get_json", fake_get_json)
    jobs = hackernews.fetch(_cfg())
    assert len(jobs) == 1
    assert jobs[0].title.startswith("Acme | Unity Dev")
    assert jobs[0].url == "https://news.ycombinator.com/item?id=1"
