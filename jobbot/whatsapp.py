"""Send job alerts to your own WhatsApp via CallMeBot (free, no business account).

Setup (one time):
  1. Save the CallMeBot number +34 684 770 005 to your phone contacts.
  2. From your WhatsApp, send it:  I allow callmebot to send me messages
  3. It replies with your personal API key.
  (CallMeBot rotates this number; if it shows as "not on WhatsApp", get the current
   one at https://www.callmebot.com/blog/free-api-whatsapp-messages/)
Then set WHATSAPP_PHONE (your number, with country code) and WHATSAPP_APIKEY.
"""
from __future__ import annotations

import time

import requests

from .job import Job

API = "https://api.callmebot.com/whatsapp.php"

# CallMeBot is rate-limited; space messages out to stay well within limits.
DELAY_SECONDS = 6


def _format(job: Job) -> str:
    # WhatsApp markup: *bold*, _italic_. Plain URLs auto-link.
    loc = f" · {job.location}" if job.location else ""
    link = f"🔗 Apply: {job.url}\n" if job.url else ""
    return (
        f"🎮 *{job.title}*\n"
        f"🏢 {job.company}{loc}\n"
        f"{link}"
        f"_via {job.source}_"
    )


def send_jobs(jobs: list[Job], phone: str, apikey: str) -> list[Job]:
    """Send each job as a WhatsApp message. Returns the jobs successfully delivered."""
    delivered: list[Job] = []
    for i, job in enumerate(jobs):
        try:
            resp = requests.get(
                API,
                params={"phone": phone, "text": _format(job), "apikey": apikey},
                timeout=30,
            )
            if resp.ok and "ERROR" not in resp.text.upper():
                delivered.append(job)
            else:
                print(f"  ! WhatsApp send failed ({resp.status_code}): {resp.text[:200]}")
        except requests.RequestException as e:
            print(f"  ! WhatsApp error: {e}")
        if i < len(jobs) - 1:
            time.sleep(DELAY_SECONDS)
    return delivered
