# 🎮 Game-Job Alert Bot

Get Unity / game-dev job postings pushed to your **Telegram, WhatsApp, and/or
Discord** within minutes of going live, so you can be one of the first to apply.

It polls multiple job sources on a schedule, filters for roles that match your
keywords, skips anything it already alerted you about, and DMs you each new match.
It runs free on **GitHub Actions** — no server, no PC required.

```
sources ─▶ fetch ─▶ keyword filter ─▶ dedup (seen.json) ─▶ Telegram + WhatsApp + Discord
```

## Sources included
| Source | Type | Notes |
|---|---|---|
| RemoteOK | JSON API | remote tech/game roles |
| We Work Remotely | RSS | programming + design feeds |
| Arbeitnow | JSON API | EU-heavy remote roles |
| Jobicy | JSON API | remote roles |
| Remotive | JSON API | remote roles, pre-searched for Unity (every 6h) |
| Himalayas | JSON API | remote roles, pre-searched for Unity (every 24h) |
| Hacker News "Who is hiring" | HN API | monthly thread, indie/startups |
| Greenhouse / Lever / Ashby | JSON API | **specific studio boards you add** — jobs land here first |
| Adzuna | JSON API | aggregator (Indeed-style), needs free key (every 6h) |
| Jooble | JSON API | aggregator, needs free key (every 24h) |

**Strict Unity:** `config.yaml` keywords are set to Unity-only (`unity`, `unity3d`,
`unity developer`, `unity engineer`) so you only get roles that actually name Unity.
Widen by adding terms (e.g. `gameplay programmer`, `game developer`) for more volume.

**Remote-only:** `remote_only: true` keeps only remote roles. A job counts as remote if
its location/title (or body, for HN/aggregators) contains remote/anywhere/distributed/
wfh/worldwide/global. Onsite & hybrid are dropped. Set `false` in `config.yaml` to include them.

**Source cadence (rate limits):** most sources are polled every run (~15 min). Remotive
(≤4/day), Himalayas (24h cache), and the aggregators self-throttle (Remotive 6h, Himalayas
24h, Adzuna 6h, Jooble 24h) via `source_state.json`, committed back each run like `seen.json`.
Reddit and Hitmarker were dropped — Reddit blocks datacenter IPs (GitHub Actions) with
`403`, and Hitmarker has no public API.

## Notifications you can get

Pick any one, or run several at once — the bot delivers each new match to **every
channel you've configured**. All three options are completely free.

| Channel | How it reaches you | What it costs | Setup effort | Best for |
|---|---|---|---|---|
| **Telegram** | DM from your bot | Free | Easy (5 min) | Instant phone + desktop alerts, rich formatting |
| **WhatsApp** (CallMeBot) | Message to your own number | Free | Easy (2 min) | Alerts in the app you already check most |
| **Discord** (webhook) | Post in a channel | Free | Easy (1 min) | A searchable feed/archive; share with friends job-hunting |

Each alert includes the **role title, company, location, source, and a direct apply
link** so you can act in seconds. Duplicate postings (same role across locations) are
collapsed into one alert, and you never get the same job twice.

> If you set up **none** of them, the bot stops with a clear error — configure at
> least one channel's secrets/env vars (see steps 1, 1b, 1c below).

---

## 1. Create your Telegram bot (5 min)

1. In Telegram, open **@BotFather** → send `/newbot` → follow prompts.
   Copy the **bot token** it gives you (looks like `123456:ABC...`).
2. Open a chat with your new bot and send it any message (e.g. "hi").
   This is required before the bot can DM you.
3. Get **your chat id**: open this URL in a browser (paste your token):
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   Find `"chat":{"id":123456789` — that number is your `TELEGRAM_CHAT_ID`.

## 1b. (Optional) WhatsApp alerts via CallMeBot — free

You can get the same alerts on WhatsApp, in addition to or instead of Telegram.
We use **CallMeBot**, a free service (no Meta/business account needed):

1. Save this number to your phone contacts: **+34 684 770 005** (CallMeBot).
2. From your WhatsApp, send that contact the exact message:
   `I allow callmebot to send me messages`
3. It replies with **your personal API key** (a number). That's your `WHATSAPP_APIKEY`.
   (If the number ever shows as "not on WhatsApp", check the latest one at
   https://www.callmebot.com/blog/free-api-whatsapp-messages/ — CallMeBot rotates it.)
4. Your `WHATSAPP_PHONE` is your own number **with country code**, e.g. `+919876543210`.

> Notes: CallMeBot is rate-limited, so the bot spaces messages ~6s apart. It's meant
> for low-volume personal alerts — perfect here. If the key ever stops working, just
> re-send the "I allow…" message to get a fresh one.

## 1c. (Optional) Discord alerts via Incoming Webhook — free

Get the same alerts in a Discord channel. No bot to host:

1. In Discord (you need "Manage Webhooks" on the server): **Server Settings →
   Integrations → Webhooks → New Webhook**.
2. Choose the channel you want alerts in, then click **Copy Webhook URL**.
3. Set `DISCORD_WEBHOOK_URL` to that URL.

Jobs arrive as tidy clickable embeds (batched up to 10 per message).

## 1d. (Optional) More volume — Adzuna + Jooble aggregators (free keys)

These aggregate listings from across the web (Indeed-style coverage). They stay **off**
until their keys are set, then self-throttle (Adzuna 6h, Jooble 24h) to respect free quotas.

- **Adzuna:** register at https://developer.adzuna.com → get **app id** + **app key** →
  set `ADZUNA_APP_ID` and `ADZUNA_APP_KEY`. Countries queried are in `config.yaml`
  (`adzuna_countries`, default `gb, us, in`).
- **Jooble:** register at https://jooble.org/api/about → get an **API key** →
  set `JOOBLE_API_KEY`.

Both are queried for "unity developer"; the strict-Unity + remote filters still apply.

## 2. Test locally (optional but recommended)

```powershell
# from the game-job folder, with a venv active
pip install -r requirements.txt

# set secrets for this PowerShell session (set whichever channels you want)
$env:TELEGRAM_BOT_TOKEN  = "123456:ABC..."
$env:TELEGRAM_CHAT_ID    = "123456789"
$env:WHATSAPP_PHONE      = "+919876543210"   # optional
$env:WHATSAPP_APIKEY     = "123456"          # optional (from CallMeBot)
$env:DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."  # optional

# see what WOULD be sent, without sending or touching seen.json
python main.py --dry-run

# real run — sends to whichever channels are configured
python main.py
```

### Windows / PowerShell terminal notes (important)

These are the exact gotchas to get it running on Windows PowerShell:

1. **Allow scripts in this session** (needed before activating a venv). Scoped to the
   current window only, so it's safe and reverts when you close it:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   ```
2. **Activate a virtual environment** (example uses an existing one on this machine —
   substitute your own path):
   ```powershell
   & c:\cloudsufi_code\data-hunter\.venv\Scripts\Activate.ps1
   ```
3. **If `pip` is missing in that venv** (`No module named pip`), bootstrap it once:
   ```powershell
   python -m ensurepip --upgrade
   ```
4. **If `python` isn't on PATH**, call the venv's interpreter by full path. This is how
   the bot was verified on this machine:
   ```powershell
   & c:\cloudsufi_code\data-hunter\.venv\Scripts\python.exe -m pip install -r requirements.txt
   & c:\cloudsufi_code\data-hunter\.venv\Scripts\python.exe main.py --dry-run
   ```
5. **Unicode/emoji in job titles** can crash older Windows consoles (`cp1252`); the bot
   already forces UTF-8 output, so no action needed — just don't be surprised if a raw
   `print` elsewhere complains.

> Tip: a fresh, dedicated venv avoids the `pip` issue entirely:
> `python -m venv .venv ; & .\.venv\Scripts\Activate.ps1 ; pip install -r requirements.txt`

## 3. Deploy free on GitHub Actions

1. Create a **new GitHub repo** and push the contents of this `game-job` folder
   to it (this folder is the repo root, so `.github/` sits at the top).
2. In the repo: **Settings → Secrets and variables → Actions → New repository secret**.
   Add the channels you want (one, the other, or both):
   - Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`
   - WhatsApp: `WHATSAPP_PHONE` (with country code), `WHATSAPP_APIKEY` (from CallMeBot)
   - Discord: `DISCORD_WEBHOOK_URL`
   - (optional) Adzuna: `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` · Jooble: `JOOBLE_API_KEY`
3. **Actions** tab → enable workflows → open **job-alerts** → **Run workflow**
   to test immediately. After that it runs automatically every 15 minutes.

That's it. New matching jobs arrive on your chosen channels. The bot commits
`seen.json` (dedup) and `source_state.json` (per-source poll timers) back to the
repo each run, so you never get duplicates and rate-limited sources stay throttled.

---

## Tuning what you receive — `config.yaml`

- **`keywords`** — a job is kept if its title/tags/description contains ANY of these.
  Add/remove to widen or narrow. Start broad, then trim noisy terms.
- **`exclude`** — drop roles you can't apply to (e.g. `principal`, `director`).
- **`remote_only`** — `true` keeps only remote roles. Remote-only boards always pass;
  studio/HN roles must say "remote" in location/title (onsite/hybrid are dropped). Set
  `false` to include onsite/hybrid.
- **`seen_retention_days`** — how long a job stays "seen" before it could re-alert.

## Adding game studios (highest-value step) — `config.yaml` → `studios`

Studio boards post **before** LinkedIn. Add the studios you'd love to work at.
Find a studio's board type and token from its careers page URL:

| If careers URL looks like… | Put under | Token to use |
|---|---|---|
| `boards.greenhouse.io/riotgames` | `greenhouse:` | `riotgames` |
| `jobs.lever.co/studioname` | `lever:` | `studioname` |
| `jobs.ashbyhq.com/studioname` | `ashby:` | `studioname` |

Verify a token works by opening the API URL in a browser, e.g.
`https://boards-api.greenhouse.io/v1/boards/riotgames/jobs` — if you get JSON, it's good.
Bad tokens are skipped with a warning; they won't break the run.

## Job-hunting tips to pair with this bot
- **Apply within the first hour** — the bot's whole point. Keep a tailored Unity
  CV + a 3-line cover note ready to paste.
- **Maintain a portfolio link** (itch.io build + GitHub) in your alert-response template.
- **Add 10–20 dream studios** to `studios:` — that's where you'll beat the crowd.
- Widen `keywords` gradually; too-broad terms like bare `c#` flood you with non-game roles.

## Troubleshooting
- *No Telegram message*: confirm you messaged the bot first (step 1.2) and the
  chat id is correct. Run `python main.py` and read the printed errors.
- *A source errors*: it's logged and skipped; other sources still run.
- *Too few jobs*: broaden `keywords` and add studio boards. Too many: tighten `exclude`.
