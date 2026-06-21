"""Notifier formatting: empty url must not break payloads."""
from jobbot import discord, telegram, whatsapp
from jobbot.job import Job


def test_discord_embed_omits_empty_url():
    with_url = discord._embed(Job(title="Unity Developer", company="x",
                                  url="https://x/1", source="RemoteOK"))
    without = discord._embed(Job(title="Unity Developer", company="x",
                                 url="", source="RemoteOK"))
    assert with_url["url"] == "https://x/1"
    assert "url" not in without  # empty url omitted -> Discord won't 400 the batch


def test_text_notifiers_skip_empty_link():
    job = Job(title="Unity Developer", company="x", url="", source="RemoteOK")
    assert "Apply" not in telegram._format(job)
    assert "Apply" not in whatsapp._format(job)
    job2 = Job(title="Unity Developer", company="x", url="https://x/1", source="RemoteOK")
    assert "https://x/1" in telegram._format(job2)
    assert "https://x/1" in whatsapp._format(job2)
