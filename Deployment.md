# Deployment Guide

How to stand Second Brain up on a fresh machine, starting from nothing but
the Obsidian vault itself. Written after the first real install (this
machine, a locked-down corporate laptop) — the ordering and the
workarounds below reflect what actually happened, not a clean-room guide.

There are two independent systems to deploy, in this order:

1. **Hermes** — the messaging/cron agent that does all live capture and
   enrichment (email, meetings, company tagging, summaries). Runs
   entirely outside this repo, in `%LOCALAPPDATA%\hermes`.
2. **Second Brain** — this repo. A FastAPI backend + React frontend that
   reads/serves the vault and triggers Hermes's cron jobs on demand. Does
   **not** do its own capture anymore — that moved fully to Hermes.

Do Hermes first. Second Brain's My Day refresh button and several
Pipelines assume Hermes cron jobs already exist.

---

## 1. Hermes Deployment

### What "no admin rights" forces

This machine has no local-admin rights, and every plain installer or
package manager that wants elevation is a dead end. The workaround that
actually worked: **everything lives under `%LOCALAPPDATA%\hermes`**, a
user-writable path that needs zero elevation —

- Hermes Agent itself: a plain `git clone` of the `hermes-agent` repo to
  `%LOCALAPPDATA%\hermes\hermes-agent`, not an installer/MSI.
- Its own Python 3.11 runtime + dependencies: a **local venv managed by
  `uv`** (`hermes-agent/venv`), created by the repo's own
  `setup-hermes.sh` — never a system Python install.
- The `hermes` CLI command: added to the **User** `PATH` environment
  variable (`[Environment]::SetEnvironmentVariable('Path', ..., 'User')`),
  never the System `PATH` — setting the User variable doesn't need
  elevation, setting System does.

### Real install steps

```powershell
# 1. Clone hermes-agent under a writable, non-Program-Files path
git clone <hermes-agent-repo-url> "$env:LOCALAPPDATA\hermes\hermes-agent"
cd "$env:LOCALAPPDATA\hermes\hermes-agent"

# 2. Run the bundled setup script (creates the uv-managed venv, installs
#    deps, symlinks the `hermes` command into a user bin dir)
bash setup-hermes.sh

# 3. Confirm it's really on PATH and really runs
hermes --version
```

If `git`/`bash`/`uv` themselves aren't available and can't be installed
(same admin-rights wall), Git for Windows and a portable `uv.exe` both
have no-admin, user-scope installers — install those first, same
principle: user-writable paths, User `PATH` only.

**Known trap:** a bare `python`/`python3` on this machine's `PATH` may
resolve to the **Microsoft Store execution-alias stub**
(`AppData\Local\Microsoft\WindowsApps\python.exe`), which prints "Python
was not found; run without arguments to install from the Microsoft
Store" instead of actually running anything — it is not a real
interpreter. This bit us more than once mid-session when invoking a
Hermes-deployed script directly (outside the Hermes CLI's own venv). Find
the real interpreter with `py -0p` (lists every real registered install)
rather than trusting a bare `python` call, or point directly at
`hermes-agent`'s own venv (`hermes-agent\venv\Scripts\python.exe`) when
you specifically need Hermes's own environment.

### The gateway (cron scheduler) — the real nightmare

`hermes gateway install` wants to register a **systemd/launchd-style
background service** — the closest Windows equivalent is a Scheduled
Task, and creating a real one that survives a reboot requires the same
elevation this machine doesn't have.

**Workaround used here:** a Windows **Startup-folder login item** instead
— a `.vbs` launcher script dropped into
`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\`
(`Hermes_Gateway.vbs`; a second one per additional profile that needs its
own gateway, e.g. `Hermes_Gateway_meeting-prep-agent.vbs`) that starts
`hermes gateway run` silently on login.

```powershell
hermes gateway install    # attempts the real service; on this machine,
                           # falls back to / needs to be paired with the
                           # Startup-folder .vbs approach above
hermes gateway status      # confirms it's actually running + heartbeat
```

**This is a known, disclosed, still-open gap, not a solved problem:** a
Startup-folder item only fires on interactive login, not on a true
reboot-to-service basis, and it was found *down* twice during real usage
(once from a stale prior state, once after an actual machine restart) —
each time silently, with no error surfaced anywhere except "cron jobs
just aren't firing." **After setting this up on the new laptop, don't
assume it's durable — check `hermes gateway status` after every reboot
until a real elevated Scheduled Task becomes possible** (e.g., if IT
grants a one-time elevated session to register it properly, that's worth
doing instead of this fallback).

### If the antivirus/Defender flags it

**What actually happened on this install:** it was **scripts/PowerShell
getting flagged, not `hermes.exe` itself** — something in `setup-hermes.sh`'s
own execution, or a Skill script's invocation, tripped AMSI or a
script-execution policy, not a binary-signature detection. The exact
remediation wasn't preserved, but given it's a script-execution flag
rather than a file-quarantine, the first things to check on the new
laptop are:

- Current PowerShell execution policy (`Get-ExecutionPolicy`) — if it's
  `Restricted`/`AllSigned`, a user-scope `Set-ExecutionPolicy -Scope
  CurrentUser -ExecutionPolicy RemoteSigned` may be enough, no admin
  needed.
- Whether it's AMSI specifically flagging script *content* (a real AV
  console/event log entry naming AMSI, not just "blocked") rather than
  execution policy — that needs an IT-side AMSI exclusion, not something
  fixable user-side.

*(Once you've actually hit and solved this again, replace this
paragraph with the real fix — this is a starting point, not a verified
replay.)*

### If network/proxy blocks downloads

Also a real blocker during the original install, but neither of us
remembers the exact mechanism or fix well enough to write it down
correctly — rather than guess, **troubleshoot it live if it recurs on
the new laptop**, then come back and replace this section with what
actually worked. Starting points worth checking first: a corporate
proxy env-var convention (`HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`) IT may
already push via GPO; `git config http.proxy` / `npm config set proxy`
if it's tool-specific rather than system-wide; and whether it's actually
TLS interception (a corporate root CA needs adding to git/Node/Python's
trust store) rather than a plain proxy address problem, if the failure
looks like a certificate error rather than a connection timeout.

---

## 2. Hermes Config

### Compass (the company LLM gateway)

"Compass" is the same internal LLM endpoint both Second Brain's own
backend and every Hermes profile's model calls use — one company gateway,
two consumers. Hermes needs its own model pointed at it:

```powershell
hermes setup model      # interactive: point the default model/provider at Compass
# or non-interactively, whatever the real provider/base-url/key values are
hermes model            # confirm/select after setup
```

Every specialist profile created via `--clone` (see below) inherits
whatever model/provider the `default` profile has configured — set
Compass up on `default` first, before cloning any specialists.

### WhatsApp (QR-code pairing)

This install uses personal WhatsApp linked like WhatsApp Web, not the
Business Cloud API:

```powershell
hermes whatsapp          # prints a QR code — scan it from the WhatsApp
                          # mobile app (Linked Devices → Link a Device)
```

The session persists locally after that (no re-scan needed until the
link is manually revoked or expires). Real chat/channel routing state
lives in `%LOCALAPPDATA%\hermes\channel_directory.json` — don't hand-edit
it; it's maintained by Hermes itself as conversations happen.

### Provisioning a profile (specialist agent)

Every specialist this vault uses (`opp-manager`, `files-manager`,
`notes-manager`, `meeting-prep-agent`, the various `*-expert` profiles,
etc.) follows the same real pattern:

```powershell
hermes profile create <name> --clone   # clones `default`'s full config
                                        # (model, all 80+ bundled skills,
                                        # full CLI toolset)
```

A fresh clone inherits **everything** — trim it down to only what that
specialist actually needs:

- **Remove skills it shouldn't have.** A cloned profile's `skills/`
  folder holds every skill by default. Move ones it doesn't need into a
  sibling `_disabled-skills/` (or `_disabled-skills-on-primary/` on
  `default` itself) folder rather than deleting them — this vault's own
  convention, so they're easy to re-enable later. `hermes skills
  opt-out --remove --yes` only strips *bundled* skills; a Skill copied in
  from this repo's own `Hermes-Provisioning/skills/` needs direct
  filesystem removal from the cloned profile's own `skills/` tree.
- **Strip write/tool capability for a bounded relay target.** A profile
  meant only to be reached via one-shot `hermes -p <profile> chat -q
  "..."` (with everything it needs already in the question text, no tool
  use expected) should have its `skills/` directory emptied entirely and
  `config.yaml`'s `platform_toolsets.cli` set to `[]` — this makes "can't
  write to the vault" a real structural property, not just a prompt
  instruction a model could deviate from.
- **Author a real `SOUL.md`** for the profile's own actual job — this is
  its system prompt; copy an existing similar profile's `SOUL.md` as a
  starting point rather than writing one from scratch.

### Deploying this repo's own Skills to a profile

Anything under `Hermes-Provisioning/skills/` in this repo is **inert
until manually copied** to the real profile(s) that need it — editing a
file in this repo does nothing to a live Hermes install by itself:

```powershell
# Canonical source (this repo) -> real deployed location
Copy-Item -Recurse `
  "Hermes-Provisioning\skills\<group>\<skill>" `
  "$env:LOCALAPPDATA\hermes\profiles\<profile>\skills\<group>\<skill>" `
  -Force
```

Some shared engine files (`vault_manager.py`, `vault_lib.py`) are
physically duplicated into *every* Skill folder that uses them (no
package-import mechanism across the repo/Hermes-profile boundary) — when
one of those changes, it needs re-copying to every real deployed location
that has its own copy, not just one.

### Cron jobs

```powershell
hermes -p <profile> cron create "every 20m" --prompt "..." --skill <skill-name>
```

**Two real traps, hit live on this install:**

- **Schedule string syntax:** a bare duration (`"20m"`) creates a
  **one-time** job (fires once, done, regardless of `--repeat`); only the
  `"every "`-prefixed form (`"every 20m"`) creates a real recurring
  interval job. The CLI's own success output looks identical either way
  (`"Schedule: once in 20m"` vs. `"Schedule: every 20m"`) — read that
  line, or the raw `cron/jobs.json` entry, before trusting a newly
  created job is actually recurring.
- **`--repeat` semantics:** an integer caps the job at that many total
  runs, after which it goes `disabled`/`state: completed` and needs a
  human to notice and re-enable it — fine for a genuine one-time backfill,
  wrong for anything meant to be a standing pipeline. `--repeat 0` clears
  the cap to unbounded (`repeat.times: null`) — the shape every
  standing/recurring job (email capture, thread/file summarization)
  should actually use, matching this vault's own `email-delta-capture`
  job.

A new job's `--skill` only resolves against the **primary/default
profile's** own enabled-skill catalog, regardless of which profile's own
`scripts/` folder the code physically lives in — a Skill that currently
lives only under a specialized profile needs to *also* be enabled on
`default` (moved out of its own `_disabled-skills-on-primary/` staging
folder there) before a cron job naming it via `--skill` will actually
run.

---

## 3. System Deployment (this repo)

```powershell
git clone <this-repo-url>
cd "Second Brain"

# Backend
cd src/backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt   # or however deps are pinned

# Frontend
cd ..\..\src\frontend
..\..\tools\node\npm.cmd install                # portable Node toolchain
                                                 # lives at tools/node — no
                                                 # global Node install needed
```

**Prerequisites:**

- Windows 11, PowerShell 7+.
- **Outlook desktop client**, installed and signed in — Hermes's own
  email/meeting capture drives the real running Outlook application via
  COM automation, not an API. A Microsoft 365 web-only account will not
  work.
- **An Obsidian vault directory** — bring the vault itself from the old
  laptop (it's just files; copy the folder over, no export/import step).
  There is no staging/promotion gate: the backend reads/writes it
  directly, so this should be the real vault, not a scratch copy, once
  you're confident in the setup.

**Starting it:**

```powershell
tools\run-backend.cmd     # uvicorn --reload, http://localhost:8001
tools\run-frontend.cmd    # vite dev server, http://localhost:5173
```

Or double-click `start.bat` at the repo root, which opens both in their
own console windows.

**Important — this differs from the older `Documentation/DeploymentGuide.md`:**
the backend no longer does its own capture (the APScheduler-based hourly
job described there is gone). All capture and enrichment is Hermes cron
jobs now (Section 1/2 above); the backend is a reader over the vault plus
a trigger for those cron jobs (the My Day "refresh" button fires the real
Hermes jobs and returns immediately — the actual capture happens
asynchronously on Hermes's own side).

---

## 4. System Config before first run

Copy `src/backend/.env.example` to `src/backend/.env` and fill in every
value — the backend fails to start if any are missing (`app/config.py`
has no defaults, by design):

| Variable | What it's for |
|---|---|
| `COMPASS_BASE_URL` | Base URL of the Compass LLM endpoint (same one Hermes profiles point at) |
| `COMPASS_API_KEY` | API key for Compass |
| `COMPASS_MODEL` | Model name Compass classification calls use |
| `ANTHROPIC_API_KEY` | Powers real conversational agent chat (LangGraph) |
| `ANTHROPIC_MODEL` | Anthropic model name |
| `VAULT_PATH` | Absolute path to the Obsidian vault directory (copied over from the old laptop) |
| `SELF_EMAIL` | The Outlook mailbox address capture runs against |
| `HERMES_MCP_SHARED_SECRET` | Shared secret gating the `/mcp` write-capable tool endpoint |

`.env` is gitignored — never commit it.

### First-run checklist

Do these in order — each one assumes the previous is real and working:

1. `hermes --version` succeeds, `hermes gateway status` shows **running**
   with a recent heartbeat.
2. `hermes profile list` shows every specialist profile you need
   (`default` plus however many `--clone`d ones), each with the right
   model/skills — a profile silently missing its Skill copy or still
   carrying the full unwanted skill set is easy to miss here.
3. `hermes cron list` shows the real jobs (`email-delta-capture`,
   `summarize-and-tag-threads`, `summarize-and-tag-files`,
   `new-company-discovery`, `create-companies-partners`, any
   profile-specific ones like `meeting-prep-agent`) — each `enabled:
   true`, each with the schedule you actually intended (watch for the
   `"20m"` vs. `"every 20m"` trap above).
4. Manually trigger one capture job (`hermes cron run <job-id>`) and
   confirm real output lands in the vault before trusting the schedule
   alone — don't wait 20-30 minutes hoping it fires correctly on its
   own the first time.
5. **Only then** start the Second Brain backend/frontend and confirm My
   Day / the notes browser show real, current vault content.
6. If this is meant to process an existing inbox's history (not just new
   mail going forward), run `retrofit_capture.py --vault-path <path>
   --limit <N>` once against the real vault
   (`Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/`)
   to backfill recent messages through the full pipeline — this is the
   one-off onboarding tool for exactly this situation, not something the
   standing cron jobs do retroactively.

### Troubleshooting

**Port already in use / backend won't start on 8001.** A previous
uvicorn `--reload` process can leave an orphaned worker holding the port.
Find the real live child process rather than trusting `netstat`'s
reported PID (which can be a dead parent):

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*uvicorn*" }
```

**Cron jobs registered but nothing happens.** Check `hermes gateway
status` first — the Startup-folder gateway workaround (Section 1) does
not survive every reboot; a "down" gateway with jobs that all look
correctly `enabled` in `cron list` is the single most common real cause
of "nothing's happening" on this kind of install.

**Email/meeting capture finds nothing, or errors reaching Outlook.**
Confirm Outlook is actually running and signed in to `SELF_EMAIL`'s
mailbox on this machine — COM automation talks to the live desktop
application, not a background service.

**A script invoked directly (outside `hermes -p ... chat`) fails with
"Python was not found."** You've hit the Microsoft Store execution-alias
stub (Section 1). Use `py -0p` to find a real interpreter, or the venv
under `hermes-agent\venv\Scripts\python.exe`.
