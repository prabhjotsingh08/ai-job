"""Shared HTTP helpers with bounded retry/backoff.

Sources call get_json/post_json and never handle transport errors themselves; a
transient 5xx / timeout / 429 is retried a few times here (honoring Retry-After)
before the exception propagates to collect_all, which logs + skips that source.
"""
from __future__ import annotations

import time

import requests

UA = "Mozilla/5.0 (compatible; game-job-bot/1.0; +https://github.com)"
HEADERS = {"User-Agent": UA, "Accept": "application/json"}

MAX_ATTEMPTS = 3
BACKOFF_BASE = 1.5  # seconds; doubles each retry
RETRY_STATUSES = {429, 500, 502, 503, 504}


def _retry_after(resp: requests.Response, fallback: float) -> float:
    raw = resp.headers.get("Retry-After")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return fallback


def _request(method: str, url: str, *, timeout: int, headers: dict, **kwargs):
    last_exc: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        backoff = BACKOFF_BASE * (2 ** attempt)
        try:
            resp = requests.request(method, url, headers=headers, timeout=timeout, **kwargs)
            if resp.status_code in RETRY_STATUSES and attempt < MAX_ATTEMPTS - 1:
                time.sleep(_retry_after(resp, backoff))
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.ConnectionError, requests.Timeout) as e:
            last_exc = e
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(backoff)
                continue
            raise
    # Exhausted retries on a retryable status: raise the last response's error.
    resp.raise_for_status()
    if last_exc:  # pragma: no cover - defensive
        raise last_exc
    return resp.json()


def get_json(url: str, timeout: int = 25, headers: dict | None = None):
    h = dict(HEADERS)
    if headers:
        h.update(headers)
    return _request("GET", url, timeout=timeout, headers=h)


def post_json(url: str, payload: dict, timeout: int = 25, headers: dict | None = None):
    h = dict(HEADERS)
    h["Content-Type"] = "application/json"
    if headers:
        h.update(headers)
    return _request("POST", url, timeout=timeout, headers=h, json=payload)
