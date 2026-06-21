"""Send formatted job alerts to a Telegram chat via the Bot API."""
from __future__ import annotations

import html
import time

import requests

from .job import Job

API = "https://api.telegram.org/bot{token}/sendMessage"


def _format(job: Job) -> str:
    title = html.escape(job.title)
    company = html.escape(job.company)
    loc = f" · {html.escape(job.location)}" if job.location else ""
    src = html.escape(job.source)
    link = f"🔗 <a href=\"{html.escape(job.url)}\">Apply</a>\n" if job.url else ""
    return (
        f"🎮 <b>{title}</b>\n"
        f"🏢 {company}{loc}\n"
        f"{link}"
        f"<i>via {src}</i>"
    )


def send_notice(token: str, chat_id: str, text: str) -> None:
    """Send a one-line status notice (e.g. a source failure). Best-effort; never raises."""
    try:
        requests.post(
            API.format(token=token),
            json={"chat_id": chat_id, "text": text[:4000],
                  "disable_web_page_preview": True},
            timeout=15,
        )
    except requests.RequestException as e:
        print(f"  ! Telegram notice error: {e}")


def send_jobs(jobs: list[Job], token: str, chat_id: str) -> list[Job]:
    """Send each job as its own message. Returns the jobs successfully delivered."""
    if not token or not chat_id:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID not set in environment."
        )
    url = API.format(token=token)
    delivered: list[Job] = []
    for job in jobs:
        payload = {
            "chat_id": chat_id,
            "text": _format(job),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 429:
                # Respect Telegram rate limiting and retry once.
                retry_after = resp.json().get("parameters", {}).get("retry_after", 3)
                time.sleep(retry_after + 1)
                resp = requests.post(url, json=payload, timeout=20)
            if resp.ok:
                delivered.append(job)
            else:
                print(f"  ! Telegram send failed ({resp.status_code}): {resp.text[:200]}")
            time.sleep(0.5)  # stay under ~1 msg/sec to the same chat
        except requests.RequestException as e:
            print(f"  ! Telegram error: {e}")
    return delivered
