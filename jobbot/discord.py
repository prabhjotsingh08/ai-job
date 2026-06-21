"""Send job alerts to a Discord channel via a free Incoming Webhook.

Setup (one time):
  1. In Discord: Server Settings -> Integrations -> Webhooks -> New Webhook.
  2. Pick the channel, click "Copy Webhook URL".
  3. Set DISCORD_WEBHOOK_URL to that URL.
No bot hosting and no cost — Discord just accepts POSTs to the webhook.
"""
from __future__ import annotations

import time

import requests

from .job import Job

# Discord allows up to 10 embeds per message; batching keeps us well under
# the webhook rate limit (~30 requests/min).
EMBEDS_PER_MESSAGE = 10
COLOR = 0x00B4D8  # Unity-ish cyan


def _embed(job: Job) -> dict:
    loc = f" · {job.location}" if job.location else ""
    embed = {
        "title": job.title[:256] or "(untitled role)",
        "description": f"🏢 {job.company}{loc}"[:4096],
        "color": COLOR,
        "footer": {"text": f"via {job.source}"},
    }
    # Discord rejects the whole batch (400) on an empty/invalid embed url; only set it when present.
    if job.url:
        embed["url"] = job.url
    return embed


def send_notice(webhook_url: str, text: str) -> None:
    """Post a one-line status notice (e.g. a source failure). Best-effort; never raises."""
    try:
        requests.post(webhook_url, json={"content": text[:1900]}, timeout=15)
    except requests.RequestException as e:
        print(f"  ! Discord notice error: {e}")


def send_jobs(jobs: list[Job], webhook_url: str) -> list[Job]:
    """Post jobs as batched embeds. Returns the jobs successfully delivered.

    Embeds go out per-batch, so a failed batch means none of its jobs are delivered.
    """
    delivered: list[Job] = []
    batches = [
        jobs[i : i + EMBEDS_PER_MESSAGE]
        for i in range(0, len(jobs), EMBEDS_PER_MESSAGE)
    ]
    for bi, batch in enumerate(batches):
        payload = {"embeds": [_embed(j) for j in batch]}
        try:
            resp = requests.post(webhook_url, json=payload, timeout=20)
            if resp.status_code == 429:
                retry_after = float(resp.json().get("retry_after", 2))
                time.sleep(retry_after + 0.5)
                resp = requests.post(webhook_url, json=payload, timeout=20)
            if resp.ok:
                delivered.extend(batch)
            else:
                print(f"  ! Discord send failed ({resp.status_code}): {resp.text[:200]}")
        except requests.RequestException as e:
            print(f"  ! Discord error: {e}")
        if bi < len(batches) - 1:
            time.sleep(1)  # be polite between batch posts
    return delivered
