# Hermes at Runtime — the operational surface

Hermes is the agent runtime. It owns the profiles, the prompts, the schedules and
the actual execution; Second Brain reads and annotates it.

This page is what you need to know to *operate* a live Hermes install. What the
`Hermes-Provisioning/` **folder** is for, and when to bring it back, is a
different page → **[Hermes-Provisioning.md](Hermes-Provisioning.md)**.

---

## Two commands that sound alike and are not

| Command | What it actually is |
|---|---|
| `hermes serve` | **The local API.** `127.0.0.1:9119`. This is what an app integrates against. |
| `hermes gateway` | **The messaging and cron daemon only** — its own startup banner says "Messaging platforms + cron scheduler". Not a REST API. |

Integrating against the gateway, or against a documented-but-not-installed port,
is a well-worn way to spend a day. Check the running version before trusting any
API documentation.

---

## Authentication is a session token

Not a bearer API key.

The token is always minted server-side. Historically an app fetched it by
scraping `GET /`'s HTML, which embeds `window.__HERMES_SESSION…` — but **headless
`hermes serve` no longer serves that page** (`GET /` 404s; `hermes dashboard`
still serves it). Scraping is therefore not a mechanism you can rely on.

**The supported arrangement is a shared secret set on both sides:**

| Set this | Where |
|---|---|
| `HERMES_DASHBOARD_SESSION_TOKEN` | Hermes' own root `.env` |
| `HERMES_API_KEY` | this app's `.env` |

Both to the same generated value.

> Remember that Hermes env files **do not chain** — every profile has its own
> home and its own `.env`, with no fallback to the top-level file.

---

## Two-way chat is a WebSocket, not REST

Hermes' embedded chat is newline-delimited **JSON-RPC 2.0 over one WebSocket** at
`/api/ws` — the same channel the desktop app and the in-browser Chat tab drive.

Auth reuses the same per-install session token, passed as `?token=` on the
handshake. A browser WebSocket upgrade cannot carry a custom header, so this is
the one endpoint that takes the credential as a query parameter instead of
`x-hermes-session-token`.

---

## Profiles

An Agent **is** a Hermes profile. Creating one is the first step of adding a
specialist; Second Brain's Registry only annotates what already exists.

### Cloning inherits more than you want, and less than you expect

`hermes profile create <name> --clone` copies `.env`, `config.yaml`, the full
skill set and the `platform_toolsets.cli` list from the source profile.

It does **not** carry over an already-paired platform connection. WhatsApp needs
its own interactive QR pairing per profile (`hermes -p <name> whatsapp`) before
that profile's gateway will stay running — otherwise the gateway exits
immediately with `WhatsApp enabled but not paired`, despite identical config.

It also does not create a `profile.yaml` at all. That file appears only on the
first `hermes profile describe <profile> --text "…"` call, which writes the
standing two-key shape (`description`, `description_auto: false`). Describe every
new profile; an undescribed one is invisible to anything that routes on
description text.

### Stripping a clone down to a relay target

A profile meant to be reached only by one-shot `chat -q`, with everything it
needs already in the question text, should have no tools at all. Delete the
cloned profile's entire `skills/` directory — `hermes skills opt-out --remove
--yes` strips only *bundled* skills, leaving local and project-specific ones
behind.

Do this structurally. Prose in `SOUL.md` asking an agent not to use its tools is
not a boundary.

### A prompt edit does not reach an open session

`SOUL.md` / `AGENTS.md` is injected **once at session creation and never re-read**,
and `session_reset.mode` defaults to `none` — so a WhatsApp thread can run
indefinitely on a prompt you have already changed. Send `/new` (or `/reset`) in
that specific thread to start a session that picks the edit up.

A two-day-old session asking questions from a schema you removed is this, not a
disobedient model.

---

## Cron is scoped per profile

This is the operational fact most likely to mislead you.

`hermes cron list` and `hermes cron status`, with no `-p`, show **only the default
profile's** jobs and gateway. `hermes -p <profile> cron list` shows a completely
different job set with its own separate gateway state.

The default profile's gateway being alive tells you nothing about whether another
profile's gateway is running. A job that has "vanished" is usually a job you are
looking for under the wrong profile.

Two related traps, both in `MEMORY.md` as rules:

- A bare duration (`"20m"`) creates a **one-time** job. Only `"every 20m"` recurs.
- A job's `--skill` resolves against the **running** profile's enabled skills, not
  the profile the script lives under.

### Finding out what a run actually did

Every run leaves three linked traces off the same `executions.db` row:

| Trace | Keyed on |
|---|---|
| `cron/jobs.json` | the job definition |
| `cron/output/<job_id>/<finished_at>.md` | the run's `finished_at`, as `YYYY-MM-DD_HH-MM-SS` |
| `agent.log` lines tagged `[cron_<job_id>_<started_at>]` | the run's `started_at`, as `YYYYMMDD_HHMMSS` |

Note the two different timestamps and two different formats. Match on the right
one and a run's full story is recoverable without guessing.
