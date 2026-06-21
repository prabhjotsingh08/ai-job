"""Entry point: collect jobs from all sources, filter, dedup, alert via Telegram.

Run locally:   python main.py
Dry run (no Telegram send, just print matches):  python main.py --dry-run
"""
from __future__ import annotations

import argparse
import sys

# Windows consoles default to cp1252 and choke on emoji / non-Latin job titles.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

from jobbot import discord, telegram, whatsapp
from jobbot.config import load_config
from jobbot.filters import is_remote, matches
from jobbot.schedule import SourceState
from jobbot.sources import collect_all
from jobbot.store import SeenStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Unity/game-dev job alert bot")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't send to Telegram or persist seen state; just print matches.",
    )
    args = parser.parse_args()

    cfg = load_config()
    store = SeenStore()
    source_state = SourceState()

    print("Collecting jobs...")
    all_jobs, source_errors = collect_all(cfg, source_state)
    print(f"Total fetched: {len(all_jobs)}")

    # Filter, then dedup within this run and against the seen store.
    fresh = []
    seen_this_run: set[str] = set()
    for job in all_jobs:
        if not matches(job, cfg):
            continue
        if cfg.remote_only and not is_remote(job):
            continue
        uid = job.uid
        if uid in seen_this_run or not store.is_new(uid):
            continue
        seen_this_run.add(uid)
        fresh.append(job)

    print(f"Matched keywords & new: {len(fresh)}")
    for job in fresh:
        print(f"  - {job.title} @ {job.company} [{job.source}]")

    if args.dry_run:
        print("Dry run: nothing sent, seen store untouched.")
        return

    if not (cfg.telegram_enabled or cfg.whatsapp_enabled or cfg.discord_enabled):
        raise RuntimeError(
            "No notification channel configured. Set Telegram (TELEGRAM_BOT_TOKEN + "
            "TELEGRAM_CHAT_ID), WhatsApp (WHATSAPP_PHONE + WHATSAPP_APIKEY), and/or "
            "Discord (DISCORD_WEBHOOK_URL)."
        )

    # A job counts as delivered if ANY enabled channel sent it. Only delivered jobs
    # are marked seen, so a send/network failure leaves the job to retry next run
    # instead of being silently lost.
    delivered_uids: set[str] = set()
    if fresh:
        if cfg.telegram_enabled:
            done = telegram.send_jobs(fresh, cfg.telegram_token, cfg.telegram_chat_id)
            print(f"Telegram: sent {len(done)}/{len(fresh)}")
            delivered_uids.update(j.uid for j in done)
        if cfg.whatsapp_enabled:
            done = whatsapp.send_jobs(fresh, cfg.whatsapp_phone, cfg.whatsapp_apikey)
            print(f"WhatsApp: sent {len(done)}/{len(fresh)}")
            delivered_uids.update(j.uid for j in done)
        if cfg.discord_enabled:
            done = discord.send_jobs(fresh, cfg.discord_webhook)
            print(f"Discord: sent {len(done)}/{len(fresh)}")
            delivered_uids.update(j.uid for j in done)

    # Heads-up if any source failed (e.g. an exhausted Adzuna/Jooble key) — otherwise the
    # failure is buried in the Actions log. Sent to the feed channels (not WhatsApp, which
    # is rate-limited for personal low-volume use).
    if source_errors:
        notice = "⚠️ job-alerts: {n} source(s) failed this run:\n{body}".format(
            n=len(source_errors), body="\n".join(source_errors)
        )
        print(notice)
        if cfg.discord_enabled:
            discord.send_notice(cfg.discord_webhook, notice)
        if cfg.telegram_enabled:
            telegram.send_notice(cfg.telegram_token, cfg.telegram_chat_id, notice)

    for job in fresh:
        if job.uid in delivered_uids:
            store.mark(job.uid)
    store.prune(cfg.seen_retention_days)
    store.save()
    source_state.save()


if __name__ == "__main__":
    main()
