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

### Corporate TLS interception (the G42Decrypt / Zscaler middlebox)

**Solved live 2026-08-20 — this is the verified fix, not a starting
point.** Do this *before* anything else on a new corporate laptop; it is
the single highest-value step in this document, because every failure it
causes is reported by the failing tool as something else entirely.

Outbound HTTPS on this corporate network is decrypted and re-signed by a
G42 middlebox. The real chain presented for any external host is:

```
*.<host>  →  G42Decrypt (t)  →  G42Decrypt  →  AD-EC-CA-01-CA (self-signed root)
                                               sha1 1BE89EE7E18FDB1264739C0AC1C221F93C030F18
```

Windows trusts that root, so browsers work fine. **Node does not** — it
ships its own bundled CA store and ignores the Windows store entirely.
Python has the same problem (which is why the Hermes venv carries
`pip_system_certs`). The fix for Node, set once, machine-wide:

```powershell
# Node 22.15+ only. Reads the live Windows trust store, so it keeps
# working when G42 rotates the root — no cert file to regenerate.
[Environment]::SetEnvironmentVariable('NODE_OPTIONS','--use-system-ca','User')
```

Use `'Machine'` instead of `'User'` from an elevated shell if it must
apply to every account — but **only if every Node on the box is ≥ 22.15**:
older Node *refuses to start* with an unrecognised `NODE_OPTIONS`, which
is a miserable failure to diagnose. Check with
`Get-Command node -All | ForEach-Object { & $_.Source --version }`.

Also add it to `%LOCALAPPDATA%\hermes\.env`, because Windows environment
changes don't reach already-running processes, and Hermes re-reads `.env`
via `load_dotenv` on every process start:

```
NODE_OPTIONS=--use-system-ca
```

**Fallback if `--use-system-ca` is unavailable** (Node < 22.15): export
the root CA to a PEM and point `NODE_EXTRA_CA_CERTS` at it. This is a
static snapshot and breaks silently on CA rotation, so prefer the above.

```powershell
$c = Get-ChildItem Cert:\LocalMachine\Root, Cert:\CurrentUser\Root |
     Where-Object { $_.Thumbprint -eq '1BE89EE7E18FDB1264739C0AC1C221F93C030F18' } |
     Select-Object -First 1
"-----BEGIN CERTIFICATE-----`r`n" +
  [Convert]::ToBase64String($c.RawData,'InsertLineBreaks') +
  "`r`n-----END CERTIFICATE-----`r`n" |
  Set-Content "$env:LOCALAPPDATA\hermes\corporate-root-ca.pem" -Encoding ascii -NoNewline
```

To confirm what the middlebox is actually presenting on a given host
(rather than assuming the root), connect with verification off and walk
the chain — inspection only, sends no data:

```powershell
node -e "const t=require('tls');const s=t.connect({host:'web.whatsapp.com',port:443,servername:'web.whatsapp.com',rejectUnauthorized:false},()=>{let c=s.getPeerCertificate(true),d=0;const seen=new Set();while(c&&c.subject&&!seen.has(c.fingerprint256)){seen.add(c.fingerprint256);console.log(d++,JSON.stringify(c.subject),'<-',JSON.stringify(c.issuer));if(c.issuerCertificate&&c.issuerCertificate!==c)c=c.issuerCertificate;else break;}s.destroy();});"
```

**Never fix this with `NODE_TLS_REJECT_UNAUTHORIZED=0`.** It is the top
search result for the error and it does make the symptom disappear — by
disabling certificate validation entirely, leaving the connection open to
anyone. The CA fix costs one line and keeps verification intact.

Still worth checking if the above doesn't explain a failure: the proxy
env-var convention (`HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY`) IT may push via
GPO, and `git config http.proxy` / `npm config set proxy` if it's
tool-specific rather than system-wide. A *connection timeout* points
there; a *certificate error* points at the TLS interception above.

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

> **Do the TLS-interception fix in section 1 first.** Pairing cannot
> succeed without it on a corporate machine, and every error you get
> instead will point somewhere else. This cost a full session on
> 2026-08-20 before the real cause surfaced.

This install uses personal WhatsApp linked like WhatsApp Web (a Baileys
bridge under `scripts/whatsapp-bridge`), not the Business Cloud API:

```powershell
hermes whatsapp          # interactive; needs a real TTY. Choose bot vs
                          # self-chat, then scan from the phone:
                          # Linked Devices → Link a Device
```

The QR rotates every ~20s — have the phone already on the Link a Device
screen before running it. The session persists locally afterwards (no
re-scan until the link is revoked or expires).

**Two independent enable gates, and both must agree.** Resolution lives
in `gateway/config.py`; the env var wins when it is an explicit
`true`/`false`, otherwise the YAML value stands:

| Gate | Where |
|---|---|
| `WHATSAPP_ENABLED` | `%LOCALAPPDATA%\hermes\.env` |
| `platforms.whatsapp.enabled` | `%LOCALAPPDATA%\hermes\config.yaml` |

Set both through the dashboard's own endpoint rather than by hand, so
they can't drift apart:

```powershell
# token is embedded in GET / as window.__HERMES_SESSION_TOKEN__
Invoke-RestMethod -Method Put -Uri 'http://127.0.0.1:9119/api/messaging/platforms/whatsapp' `
  -Headers @{ 'x-hermes-session-token' = $tok } -ContentType 'application/json' `
  -Body '{"enabled": true, "env": {"WHATSAPP_ENABLED": "true"}}'
```

**Enabled-but-unpaired takes the whole gateway down, not just WhatsApp.**
The adapter treats a missing `creds.json` as a *non-retryable* startup
conflict, so the gateway exits (code 78) and every other channel and all
cron jobs stop with it. If you need the gateway up before pairing is
sorted, disable WhatsApp on both gates and restart — don't leave it
enabled and unpaired.

Session credentials land in `%LOCALAPPDATA%\hermes\whatsapp\session`
(`creds.json` plus several hundred key files). Note the CLI hardcodes
that legacy path while the adapter and dashboard resolve via
`get_hermes_dir("platforms/whatsapp/session", "whatsapp/session")` — they
agree only because `get_hermes_dir` prefers the legacy location once it
has content. Harmless in practice, but don't "tidy up" by moving the
session directory.

Real chat/channel routing state lives in
`%LOCALAPPDATA%\hermes\channel_directory.json` — don't hand-edit it; it's
maintained by Hermes itself as conversations happen.

#### Troubleshooting pairing

**`Connection closed (reason: 500)` in a reconnect loop, no QR.** This is
*not* a bad session, despite 500 mapping to Baileys'
`DisconnectReason.badSession`. It is almost always the TLS interception:
Baileys wraps the WebSocket error in a Boom with a generic 500, and
`bridge.js` hardcodes `pino({ level: 'warn' })`, so the real cause
(`UNABLE_TO_GET_ISSUER_CERT_LOCALLY`) never prints. Verify the session
directory is genuinely empty before believing "bad session" — if it is,
the credentials cannot be the problem. Apply the section 1 fix.

**Dashboard QR box stays blank forever.** Same root cause. The onboarding
API reports `status: "waiting"` with `qr_payload: null` indefinitely,
because the bridge it spawned died on the TLS handshake and emitted a
`disconnected` event rather than a `qr` one. The CLI gives better signal
than the dashboard here.

**`reason: 408` once, then QR appears.** Benign — the previous QR expired
unscanned. Baileys refreshes automatically; just scan the new one.

**`WHATSAPP_ENABLED=WHATSAPP_ENABLED` in `.env`.** A real dashboard-toggle
bug seen on 2026-08-20: it wrote the *key name* as the value. That string
is neither truthy nor an explicit false, so resolution silently falls
through to the YAML gate and the toggle appears to do nothing. Check the
literal value if enabling from the dashboard seems to have no effect.

Confirm it actually came up:

```powershell
(Invoke-RestMethod http://127.0.0.1:9119/api/status).gateway_platforms
# expect: whatsapp = @{ state = connected; error_code = }
```

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
