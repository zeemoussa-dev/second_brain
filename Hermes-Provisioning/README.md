# Hermes Provisioning

Everything needed to configure a Hermes install from scratch, prepared and
version-controlled here in Second Brain, then applied to a real Hermes
instance. Purpose (operator, 2026-08-20): so Hermes can be redeployed in
seconds instead of manually rediscovering the same setup steps and bugs
every time — Hermes itself lives outside this repo (see the "where to
install Hermes" decision in `Implementation/Plans/2026-08-20-backend-
architecture-redesign.md`), but its *configuration* is worth tracking here
since it's exactly the kind of thing that's easy to lose and expensive to
rediscover.

**Workflow:** edit/add files here → apply them to a real Hermes install
(manually today, via its own CLI/config file — no automated "push" script
exists yet, deliberately: applying config is still the operator's own
action, same discipline as running any other `hermes` CLI command
throughout tonight's session) → note what was actually applied in this
file's own "Applied" log below, so this folder never silently drifts from
the real Hermes install's actual state.

## Structure

- `config/` — `config.yaml` snippets to merge into a real Hermes install
  (never a full config.yaml — just the specific entries this repo knows
  about and has verified).
- `mcp-servers/` — declared MCP server registrations (what `hermes mcp add`
  commands to run), matching what's actually registered.
- `cron/` — declared scheduled jobs (what `hermes cron create` commands to
  run) — empty so far, no cron job has actually been created yet.
- `skills/` — `SKILL.md` files authored for Hermes, matching Hermes' own
  real `skills/<category>/<skill-name>/SKILL.md` structure so they can be
  copied in directly — empty so far, no Skill has been authored yet.

## Applied so far (2026-08-20/21)

- `config/custom_providers.yaml` — Compass provider, INCLUDING the fix for
  the base_url double-append bug (see `MEMORY.md`/plan doc for the full
  story) — applied and confirmed working live.
- `mcp-servers/outlook.yaml` — the real `outlook` MCP server, applied via
  `hermes mcp add outlook --url http://127.0.0.1:8000/tools/outlook` and
  confirmed present via `hermes mcp catalog`. As of 2026-08-21 this only
  exposes `gather_emails` (Second Brain's own internal scheduler pull,
  never actually called over MCP) — see that file's own header for
  whether this registration is worth keeping at all.
- `mcp-servers/vault.yaml` — **removed 2026-08-21**, never applied. Its
  5 Actions moved to the Skill itself (below) — see "MCP server vs.
  Hermes-native Skill scripts" in `Implementation/Plans/2026-08-20-
  backend-architecture-redesign.md` for the full decision.
- `skills/vault-rebuild/email-thread-capture/` — **rewritten 2026-08-21,
  fully self-hosted.** No MCP server, no Second Brain backend process
  involved at all. `SKILL.md` + a `scripts/` folder (8 standalone Python
  files: `vault_lib.py`, `outlook_lib.py`, and one CLI entry point per
  Action) live together as one unit, invoked entirely through Hermes'
  own `terminal` tool. Copied into the real Hermes install
  (`<hermes_home>/skills/vault-rebuild/email-thread-capture/`, plain
  file copy, `SKILL.md` + `scripts/*.py`). Requires `pywin32` importable
  by whatever Python the `terminal` tool runs (`pip install pywin32` if
  missing — see the Skill's own Prerequisites). **Not yet run.**

## Running the one-time vault rebuild

The pipeline now needs nothing from Second Brain's own backend running —
just Outlook desktop open on this machine and the Skill's own
Prerequisites satisfied (pywin32 importable). It's a real, long-running,
real-side-effect action (pulls the FULL email history, writes real vault
data) — deliberately left as a command for the operator to run, not
something triggered automatically:

```
hermes cron create 1m "Run the email-thread-capture skill: pull the full Outlook history, page by page, ingesting every email into the vault. Do not stop until a page comes back empty." --repeat 1 --skill email-thread-capture --name vault-rebuild
```

`1m` is the real one-shot schedule syntax (`hermes cron create --help`,
confirmed live 2026-08-21) — `"in 1 minute"`, documented here
originally, was never actually valid (`Failed to create job: Invalid
schedule 'in 1 minute'`). Accepted forms: a bare duration (`30m`/`2h`/
`1d`, one-shot), `every <duration>` (recurring), a cron expression, or an
ISO timestamp. `--repeat 1` makes this fire once, not recur. Progress can
be watched via `hermes cron jobs`/`hermes cron runs vault-rebuild` or the
dashboard UI's own Sessions view.

**Run 2026-08-21:** job `c5e20c740835`, scheduled successfully, first run
2026-08-21T15:07:23+04:00.
