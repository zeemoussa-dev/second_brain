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

## Where this deployment actually stands (2026-09-03, second machine)

Live status of the fresh corporate laptop, so the next session doesn't
have to rediscover it. Update this block as it moves.

**Done — Hermes is installed and healthy:**

- Hermes Agent **v0.21.0** at `%LOCALAPPDATA%\hermes`, Python 3.11.16,
  portable Node 22.23.2, uv 0.12.9, ripgrep, ffmpeg. `hermes --version`
  and `hermes doctor` both pass.
- `UV_SYSTEM_CERTS=1` persisted at **User** scope — the corporate-TLS fix
  without which nothing installs. Leave it set.
- Config migrated v0 → v40 (`hermes doctor --fix`).
- **Compass provider applied** to `config.yaml` (`model:` switched off the
  stock OpenRouter default to `compass`/`gpt-5`). Confirmed reaching
  Compass for real: Hermes has since discovered and written back the full
  Compass model catalogue (`models_discovered: true`), which only happens
  on a successful authenticated call. Note Hermes rewrites this file
  programmatically, so hand-written comments in it do not survive.
- **Gateway installed and running** via
  `hermes gateway install --start-on-login --start-now` — Startup-folder
  login item (UAC declined), gateway process up, log healthy.
- **Backend and frontend both build and run** (§3). Backend venv on
  Python 3.11.16 with all deps installed; started through the fixed
  `tools\run-backend.cmd` and `GET /health` returned
  `{"status":"ok"}`. Frontend: `tools\node` populated (Node 22.23.2 /
  npm 10.9.8), 134 packages installed, dev server served HTTP 200 on
  5173 via `tools\run-frontend.cmd`. Both were stopped again afterwards —
  nothing is left running.
- **`tools\*.cmd` launchers repaired** — they all hardcoded the first
  machine's path and could never have worked here (§3).
- **`requirements.txt` pinned `mcp<2`** — an unpinned `mcp` broke the
  backend outright on a fresh resolve (§3).

**Not done — each needs the operator personally, and each blocks what
follows it:**

1. **WhatsApp pairing** (`hermes whatsapp`) — needs a QR scan from the
   phone, and must be run from a real interactive terminal. Blocked on
   2026-09-03 by `Connection closed (reason: 500)`; the cause and fix are
   the corporate TLS interception (§1) — `NODE_OPTIONS=--use-system-ca`
   is now set both as a User variable and in `%LOCALAPPDATA%\hermes\.env`,
   and the gateway restarted. **Still to be confirmed from the operator's
   own shell** — see the shell-asymmetry warning in `MEMORY.md`: verifying
   this from a tool shell that is not behind the interception produces a
   confident false pass.
   Not a blocker for capture — the gateway runs cron jobs with no
   messaging platform enabled. Do **not** enable WhatsApp before pairing
   succeeds: enabled-but-unpaired takes the whole gateway down (§2).
2. **Let the vault finish syncing** before any capture or cron job runs.
3. Specialist profiles, Skill deployment, cron jobs — §2, in that order.

**Second Brain's own `.env` is complete.** Backend verified booting
against it — `GET /health` → `{"status":"ok"}`. `COMPASS_BASE_URL` carries
the full-completions form, `COMPASS_API_KEY` and `SELF_EMAIL` are set,
`VAULT_PATH` resolves, and `SECOND_BRAIN_DATA_PATH` deliberately points
outside the synced vault.

`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` and `HERMES_MCP_SHARED_SECRET` are
intentionally left unset — they became optional on 2026-09-03 because
nothing uses them (§4 records the verification and the one security
caveat on the empty MCP secret).

**Vault located, but it was still syncing when set.**
`C:\Users\mahmoud.moussa\OneDrive - G42\myData\Moussa Brain\second-brain`
— confirmed resolving, and `.second-brain` state will default inside it.
When first pointed at, the OKF skeleton was complete but nearly empty
(People 96, Research 3, Threads 2, everything else 0, 112 files / 0.1 MB
total, and **zero** OneDrive online-only placeholders, so it was genuine
absence rather than unfetched stubs). **Let the sync finish before running
any capture or cron job** — dedup only protects against duplicates it can
structurally see, so a half-synced vault will get duplicate notes for
everything that had not yet arrived.

**Watch the 260-char `MAX_PATH` trap here.** This vault root is already
**71 characters**, leaving ~189 for everything beneath it. Real note
paths nest deep (`Work\Threads\<thread title>\messages\<date> <HH:MM>
<sender>.md`), and on this host `Path.exists()`/`is_file()`/`is_dir()`
silently return `False` past that limit rather than raising — so an
over-long note reads as "missing" with no error anywhere. Worth
re-checking if notes start mysteriously not being found.

**Known-broken, left alone deliberately:** `npm run build` fails on 8
pre-existing TypeScript errors (§3). `npm run dev` is unaffected, which
is what the launchers and the actual workflow use.

**Machine baseline found before installing** (useful for judging whether
a future machine is comparable): Git for Windows already present
user-scope; Outlook desktop installed but not running; **no** real
Python, **no** `py` launcher, **no** Node, **no** `uv`; execution policy
`Undefined` at every persistent scope; network reachable to github.com,
nousresearch, astral.sh.

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

**Use the official installer — it works on a locked-down machine.**
Verified end-to-end on the second real install (2026-09-03, fresh
corporate laptop, no admin rights). Earlier belief that "the official
installer doesn't work here" was *almost* right but misattributed: it
fails at exactly **one** step, for a reason that has nothing to do with
admin rights (see the TLS section below), and once that one thing is
fixed it completes. Reach for the manual `git clone` route only if the
installer fails for some *other* reason.

```powershell
# 0. PREREQUISITE on a TLS-intercepting corporate network — set this
#    FIRST, before running the installer, or it will fail at the
#    "Installing Python 3.11" step. See "TLS interception" below.
[Environment]::SetEnvironmentVariable('UV_SYSTEM_CERTS','1','User')
$env:UV_SYSTEM_CERTS = '1'

# 1. Run the official installer (user-scope, no elevation)
iex (irm https://hermes-agent.nousresearch.com/install.ps1)

# 2. Confirm it's really on PATH and really runs (NEW SHELL — the
#    installer edits the User PATH, which existing shells don't see)
hermes --version
```

What the installer really does, confirmed by reading it and by watching
it run — it is **user-scope and needs no elevation**, which is why it is
viable here at all:

| It installs | Where |
|---|---|
| `uv` | `%LOCALAPPDATA%\hermes\bin\uv.exe` |
| Python 3.11 (via uv) | `%APPDATA%\uv\python\cpython-3.11...` |
| PortableGit (only if `git` is missing) | `%LOCALAPPDATA%\hermes\git\` |
| Node.js 22 LTS (portable) | `%LOCALAPPDATA%\hermes\node\` |
| `hermes-agent` repo + its venv | `%LOCALAPPDATA%\hermes\hermes-agent\` |
| ripgrep, ffmpeg (optional, via winget) | winget's own user scope |

It writes **User** `PATH` and `HERMES_HOME`/`HERMES_GIT_BASH_PATH` only,
never System, and it creates **no** service, Scheduled Task, or Startup
item — so the gateway login-item workaround below is still a separate,
manual step afterwards.

**Non-issues you will see in its output and can safely ignore:**

- `Trying SSH clone... Host key verification failed.` — expected on a
  machine with no GitHub SSH key. The installer falls back to HTTPS by
  itself and the clone succeeds. Not an error to chase.
- `[!] TUI npm install failed -- exit code` (with a *blank* exit code,
  while the captured npm output directly above it says
  `Node dependencies installed`). This is an installer bug in its own
  success-detection, not a real failure. Verify rather than assume: if
  `ui-tui\node_modules` exists, it worked. If it genuinely didn't,
  the installer prints the manual recovery itself —
  `cd "%LOCALAPPDATA%\hermes\hermes-agent\ui-tui"; npm install`.

#### TLS interception — the one real blocker (2026-09-03)

This supersedes the old speculative "If network/proxy blocks downloads"
section further down. The failure is specific and reproducible:

```
error: Failed to install cpython-3.11.16-windows-x86_64-none
  Caused by: invalid peer certificate: UnknownIssuer
```

**Why it happens, and why it is confusing:** the corporate network does
TLS interception, so every HTTPS response is re-signed by a corporate
root CA. That CA *is* in the Windows certificate store — which is why
`Invoke-WebRequest https://github.com/...` returns `200` happily, and
why `git clone` over HTTPS works fine. But `uv` is a Rust binary that
validates TLS against its **own bundled root store**, which does not
contain the corporate CA. So uv alone fails, on the exact same host that
every other tool reaches without complaint. A reachability test with
PowerShell will therefore *not* reproduce this — don't let a green
connectivity check talk you out of this diagnosis.

**Fix:** tell uv to use the Windows certificate store instead of its
bundled one.

```powershell
[Environment]::SetEnvironmentVariable('UV_SYSTEM_CERTS','1','User')
```

Set it at **User** scope (no elevation), not just for the current shell:
uv runs again later for dependency installs, and Hermes itself may
invoke it after install. Naming note: the variable used to be
`UV_NATIVE_TLS`, which still works but now prints
`the UV_NATIVE_TLS environment variable is deprecated ... Use
UV_SYSTEM_CERTS instead` — use the new name.

**This is the same middlebox documented in full under
["Corporate TLS interception (the G42Decrypt / Zscaler middlebox)"](#corporate-tls-interception-the-g42decrypt--zscaler-middlebox)
later in this section** — read that for the real chain, the thumbprint,
the Node and Python levers, and the PEM-export fallback. That section is
authoritative; the note here exists only because uv trips on it *before
you have a Hermes install at all*, so the installer fails first.

**uv is the third runtime to hit it,** after Node and Python, and it is
the one this section is about. Its tell is distinct — `invalid peer
certificate: UnknownIssuer` — and its lever is its own:

| Runtime | Tell | Lever |
|---|---|---|
| **uv** (Rust/rustls) | `invalid peer certificate: UnknownIssuer` | `UV_SYSTEM_CERTS=1` |
| **Node** | see the authoritative section | `NODE_OPTIONS=--use-system-ca` |
| **Python** | see the authoritative section | `pip_system_certs` / `SSL_CERT_FILE` |

Set it at **User** scope, not just in your shell: the gateway and its
cron jobs run detached and never see an interactive session's variables.

#### Fallback: the manual `git clone` route

Only if the official installer fails for a reason other than the TLS one
above. Needs `uv` and `bash` present already (Git for Windows supplies
bash at `%LOCALAPPDATA%\Programs\Git\bin\bash.exe`; a portable `uv.exe`
has a no-admin user-scope installer):

```powershell
git clone https://github.com/NousResearch/hermes-agent "$env:LOCALAPPDATA\hermes\hermes-agent"
cd "$env:LOCALAPPDATA\hermes\hermes-agent"
bash setup-hermes.sh   # creates the uv-managed venv, installs deps,
                       # puts the `hermes` command on the User PATH
hermes --version
```

**`setup-hermes.sh` does not finish on Windows, and does not say so**
(2026-09-04, third machine — this is why the official installer above is
now the preferred route, not just the tidier one). The script symlinks
`$SCRIPT_DIR/venv/bin/hermes`, a POSIX layout; on Windows uv creates
`venv/Scripts/hermes.exe`, so `ln` fails with `No such file or
directory`. The script runs under `set -e`, so it exits right there —
**silently skipping the bundled-skills sync that follows it**. Dependency
installation happens *before* that point, which is exactly why the run
looks successful: you get a working `hermes.exe` and an empty
`skills/` folder. There is no Windows branch in the script at all; it
only distinguishes Termux from "desktop/server", both assumed POSIX.

Two things to do by hand afterwards if you are stuck on this route:

```powershell
# 1. A .cmd shim beats a symlink here -- no Developer Mode, no elevation.
#    (Hermes also self-heals its own launchers into %LOCALAPPDATA%\hermes\bin
#    on first run, so check there before creating one.)
'@echo off'                                                  | Set-Content "$env:USERPROFILE\.local\bin\hermes.cmd" -Encoding ascii
"`"$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\hermes.exe`" %*" | Add-Content "$env:USERPROFILE\.local\bin\hermes.cmd" -Encoding ascii

# 2. Run the sync the script never reached (seeds 58 bundled skills).
cd "$env:LOCALAPPDATA\hermes\hermes-agent"
.\venv\Scripts\python.exe tools\skills_sync.py
```

**Known trap:** a bare `python`/`python3` on this machine's `PATH` may
resolve to the **Microsoft Store execution-alias stub**
(`AppData\Local\Microsoft\WindowsApps\python.exe`), which prints "Python
was not found; run without arguments to install from the Microsoft
Store" instead of actually running anything — it is not a real
interpreter. This bit us more than once mid-session when invoking a
Hermes-deployed script directly (outside the Hermes CLI's own venv).

**Correction from the 2026-09-03 install — `py -0p` is not a reliable
escape hatch.** The old advice here was to find a real interpreter with
`py -0p`. On a genuinely fresh machine there is no `py` launcher at all
(it ships with a full python.org install, which this laptop never had),
so that command fails too and tells you nothing. Before Hermes is
installed there is simply **no real Python on the machine** — the Store
stub is all you have.

Use, in order of preference:

```powershell
# 1. Hermes's own venv — what you want whenever the script is a
#    Hermes-deployed Skill script and needs Hermes's own dependencies
& "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe" --version

# 2. The uv-managed interpreter Hermes installed, for anything standalone
& "$env:LOCALAPPDATA\hermes\bin\uv.exe" python list --only-installed
```

`uv python list --only-installed` is the replacement for `py -0p` on
this machine: it lists the real, resolvable interpreter paths.

### What a good install looks like (verified 2026-09-03)

Baseline to compare against when something later seems off. Installed
version was **Hermes Agent v0.21.0 (2026.8.31)**, Python 3.11.16, install
method `git`. (Note the drift: `MEMORY.md` records `hermes-agent==0.20.4`
on the first machine. Don't assume Skill/CLI behaviour is identical
across the two installs — check before blaming a Skill.)

```powershell
hermes --version   # v0.21.0, install dir + Python version
hermes doctor      # the real health check — run it before anything else
```

**Path correction:** the `hermes` executable is at
`%LOCALAPPDATA%\hermes\bin\hermes.exe` — *not*
`%LOCALAPPDATA%\hermes\hermes-agent\bin\hermes.exe`, which is what
`Implementation/Tasks/REQ-SB-85-US-02-T01-hermes-cli-export-import-wrappers.md`
records. `hermes-agent\` is the cloned repo; `bin\` is its sibling.

**`hermes` not found right after installing?** The installer writes the
**User** `PATH`, which already-open shells never see. Open a new terminal.
To refresh inside an existing PowerShell session without restarting it:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
            [Environment]::GetEnvironmentVariable('Path','User')
```

On a healthy fresh install `hermes doctor` reports Python env, SSL CA
bundle, config files, and directory structure all ✓, and these tools
available — which is the set Second Brain's pipelines actually depend on:
`terminal`, `cronjob`, `file`, `skills`, `delegation`, `memory`,
`code_execution`, `session_search`.

**Warnings that are expected and safe to ignore on this deployment:**

- Every unconfigured auth provider (Nous Portal, OpenAI Codex, MiniMax,
  xAI) and every tool marked `system dependency not met` (`vision`,
  `tts`, `image_gen`, `spotify`, `discord`, …). None are used here.
- `Playwright Chromium not installed` — browser tools only.
- The npm advisories in `agent-browser` / `web` workspaces. Optional
  browser tooling, off the Outlook/cron path. `hermes doctor --fix`
  deliberately leaves these; they need a manual `npm audit fix`.

**One thing genuinely worth fixing on a fresh install:** `hermes doctor`
reports `Config version outdated (v0 → v40)`. Fix it immediately, before
creating profiles or cron jobs, so everything downstream is authored
against the current schema:

```powershell
hermes doctor --fix    # migrates the config; reports what it couldn't fix
```

**Do not run `--fix` unattended, and do not assume it returns.** On
2026-09-04 it started a **dashboard and a gateway** and simply kept
running — the migration is not a short, self-terminating command. Left in
a background shell it looked like a hang; what it had actually done was
leave `hermes.exe dashboard` and two `gateway run` processes live, which
then held `%LOCALAPPDATA%\hermes` open and blocked a later reinstall
until they were stopped (`hermes gateway stop`, then kill the survivors).

**Plain `hermes doctor` also gets much slower once Node is on `PATH`.**
It runs `npm audit` across the `agent-browser`/`web` workspaces, so a
machine with no Node finishes in seconds and the *same* machine finishes
in minutes after Node appears — the check did not break, it simply
started doing more. Beware of measuring this through a pipe: `hermes
doctor | Select-Object -First 50` closes the pipe early and kills the
process, so it *looks* fast while never actually completing. Redirect to
a file if you want the real runtime and the real full output.

#### Installing non-interactively? Two real gotchas

Only relevant when driving the installer from a script or an automation
tool rather than typing it into a real terminal:

- **Pass `-SkipComputerUse -SkipSetup` and the two hangs below never
  happen** (2026-09-04, third machine). The installer takes real
  parameters, so the `cua-driver` hang described next is avoidable rather
  than something to detect and kill, and `-SkipSetup` skips the
  interactive wizard that a non-interactive shell cannot answer anyway.
  Getting the file so you can pass flags to it also sidesteps a second
  problem: the canonical `iex (irm ...)` one-liner is blind remote code
  execution, which agent/automation sandboxes routinely refuse. Download,
  check, then run:

  ```powershell
  $dest = "$env:TEMP\hermes-install.ps1"
  Invoke-WebRequest 'https://hermes-agent.nousresearch.com/install.ps1' -OutFile $dest
  (Get-FileHash $dest -Algorithm SHA256).Hash   # 245 KB on 2026-09-04
  & $dest -SkipComputerUse -SkipSetup
  ```

  This run exited **0** — no hang, no killed child, nothing to diagnose.

- **It can hang forever at `Installing Computer Use driver
  (cua-driver)`.** Only if you did *not* pass `-SkipComputerUse` above.
  That step spawns `powershell.exe -Version 5.1 -s`
  (stdin/server mode), which blocks reading standard input that never
  arrives. Symptom: zero output for many minutes, and the child process
  burning ~0 CPU. `cua-driver` is desktop-control tooling that this
  deployment does not use — killing that child process lets the installer
  finish normally. Diagnose with:

  ```powershell
  Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'powershell' } |
    Select-Object ProcessId, ParentProcessId, CreationDate, CommandLine
  ```

- **A non-zero exit code does not mean the install failed.** This run
  exited `1` because of that killed optional step plus the cosmetic npm
  false-failure, while having installed everything correctly. Judge by
  `hermes --version` and `hermes doctor`, not by the exit code.

### The gateway (cron scheduler) — the real nightmare

`hermes gateway install` wants to register a **systemd/launchd-style
background service** — the closest Windows equivalent is a Scheduled
Task, and creating a real one that survives a reboot requires the same
elevation this machine doesn't have.

**Update 2026-09-03 — you no longer hand-author the `.vbs`.** Hermes
v0.21.0 does the whole fallback itself. Run one command:

```powershell
hermes gateway install --start-on-login --start-now
hermes gateway status     # confirms login item + running PID
hermes gateway list       # per-profile view
```

The elevation wall is still real — that part of the old note was
correct. What changed is that the CLI now detects it and degrades
gracefully instead of leaving you to build the workaround by hand. The
real output on this machine:

```
↻ Scheduled Task install may need administrator approval on this Windows account.
  Open the UAC prompt now? [y/N]:
  Skipped elevation. Falling back to Startup folder.
✓ Installed Windows login item: ...\Startup\Hermes_Gateway.vbs
✓ Gateway started via direct spawn (PID 23200)
```

**Answer `y` if you can.** The prompt offers a real UAC elevation, and
if you have any way to approve it (your own admin, or IT granting a
one-time elevated session) you get a genuine Scheduled Task instead of
the login-item fallback — which is the durable fix the old note below
was waiting for. Answering `N`, or running non-interactively (where
stdin is empty and it auto-skips, as happened here), gets the fallback.

**What it actually builds** — worth knowing, because debugging a silent
gateway means knowing which link broke:

| File | Role |
|---|---|
| `%APPDATA%\...\Startup\Hermes_Gateway.vbs` | Login-triggered shim. Checks the target exists, then launches it hidden (`WScript.Shell.Run ..., 0, False`). |
| `%LOCALAPPDATA%\hermes\gateway-service\Hermes_Gateway.vbs` | The real launcher it delegates to. |
| `%LOCALAPPDATA%\hermes\gateway-service\Hermes_Gateway.cmd` | Sets `HERMES_HOME`, `VIRTUAL_ENV`, `PYTHONPATH`, then runs `venv\Scripts\python.exe -m hermes_cli.main gateway run`. |

Two useful properties of that chain: it invokes the **venv Python
directly**, so a broken/unset `PATH` cannot stop the gateway starting;
and it runs through `wscript.exe`, so **PowerShell execution policy is
irrelevant** to it (which is why `.vbs` was the right choice).

**A healthy gateway log** (`%LOCALAPPDATA%\hermes\logs\gateway.log`)
shows the control pipe listening, turn machinery warmed, housekeeping
started, and — expected before WhatsApp is paired:

```
WARNING gateway.run: No messaging platforms enabled.
INFO    gateway.run: Gateway will continue running for cron job execution.
```

That warning is **not** a problem. Cron execution is exactly what
Second Brain needs from the gateway; messaging platforms are additive.

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

Getting to that real Scheduled Task no longer needs any manual task
authoring — just re-run `hermes gateway install --force --start-on-login`
in an interactive terminal during an elevated session and answer `y` to
the UAC prompt. Until then the login-item caveat above stands in full,
and `hermes gateway status` after a reboot remains the check that
matters, because a down gateway is silent: every cron job still looks
correctly `enabled` in `hermes cron list` while nothing runs.

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

**2026-09-03 update — it did not recur.** The second from-scratch
install on a fresh corporate laptop hit no antivirus, AMSI, or
execution-policy interference at any point: the installer, its bundled
`setup-hermes.sh`, winget, and every spawned script ran unimpeded, with
the execution policy left at its stock `Undefined` (no
`Set-ExecutionPolicy` was needed). So this is *not* a reliable,
every-machine blocker — treat it as something that happened once and may
not happen again, and don't pre-emptively change execution policy or
raise an IT ticket for it before actually seeing a failure.

Worth knowing if it does resurface: the one component that runs a
`.vbs` at login is the gateway workaround below, which is a different
mechanism from anything the installer executes — so an AV problem at
install time and an AV problem at gateway-startup time are separate
diagnoses, not the same one.

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
two consumers. Hermes needs its own model pointed at it.

**Do this by editing `config.yaml` directly, not through `hermes setup
model`.** Registering a *custom* (Compass-shaped) provider is not exposed
as a documented non-interactive CLI flag — this repo's own
`Hermes-Provisioning/config/custom_providers.yaml` is the verified,
already-proven mechanism, and is the intended reuse point. A fresh
install ships pointing at OpenRouter
(`model.default: anthropic/claude-opus-4.6`), so this is a real change,
not a no-op.

**Step 1 — merge the provider entry into
`%LOCALAPPDATA%\hermes\config.yaml`.** Back the file up first
(`copy config.yaml config.yaml.pre-compass.bak`), then replace the whole
stock `model:` block with:

```yaml
model:
  default: gpt-5
  provider: compass
  base_url: https://api.core42.ai/v1
custom_providers:
  - name: compass
    base_url: https://api.core42.ai/v1
    key_env: HERMES_CUSTOM_API_CORE42_AI_API_KEY
    model: gpt-5
```

Two traps, both already paid for once (see
`Hermes-Provisioning/config/custom_providers.yaml`'s own header):

- `base_url` **must not** end in `/chat/completions`. Hermes appends that
  itself, and the doubled path returns a real 404. Do **not** copy Second
  Brain's own `COMPASS_BASE_URL` value (which *does* include it) verbatim.
- There are two `base_url` fields for the same logical provider. Only
  `custom_providers[].base_url` is actually read when building requests
  (`auth_commands.py::_provider_base_url`); `model.base_url` is kept in
  sync by hand so the two never disagree.

**Step 2 — put the key in `%LOCALAPPDATA%\hermes\.env`** (which the
installer creates), never in `config.yaml`:

```
HERMES_CUSTOM_API_CORE42_AI_API_KEY=<the real Compass key>
```

**Step 3 — verify it actually reaches Compass** before building anything
on top of it:

```powershell
hermes model                       # should show compass / gpt-5
hermes chat -q "reply with OK"     # a real round-trip through Compass
```

Every specialist profile created via `--clone` (see below) inherits
whatever model/provider the `default` profile has configured — set
Compass up on `default` first, and confirm Step 3 passes, before cloning
any specialists. Cloning first means re-fixing the same setting N times.

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

Verified end-to-end 2026-09-03. The old version of this section said
`python -m venv` + `pip install`; neither works on a fresh machine —
there is no system Python, and pip would hit the same corporate-TLS wall
described in §1. Use uv (installed by Hermes) for both reasons.

```powershell
git clone https://github.com/zeemoussa-dev/second_brain.git
cd second_brain

# --- Backend: venv + deps, via uv -----------------------------------------
cd src\backend
$env:UV_SYSTEM_CERTS = '1'          # corporate TLS; see §1
$uv = "$env:LOCALAPPDATA\hermes\bin\uv.exe"
& $uv venv --python 3.11 .venv
& $uv pip install --python .venv\Scripts\python.exe -r requirements.txt

# --- Portable Node toolchain at tools\node --------------------------------
# /tools/node/ is gitignored: the repo expects a portable Node there, but
# does not ship one. Hermes already installed a correct Node 22 LTS, so copy
# it rather than re-downloading through the intercepted network:
Copy-Item -Recurse "$env:LOCALAPPDATA\hermes\node" "<repo>\tools\node"

# --- Frontend -------------------------------------------------------------
cd ..\..\src\frontend
..\..\tools\node\npm.cmd install
```

**Two real defects this install surfaced.** Both are repo bugs a fresh
machine exposes and an existing one hides:

1. **`requirements.txt` had `mcp` unpinned** — a fresh resolve now pulls
   **mcp 2.x**, which renamed `FastMCP` to `MCPServer`. The backend then
   dies on import at
   `app/data_access/system/tools/registry.py`'s `from mcp.server.fastmcp
   import FastMCP`. **Fixed** by pinning `mcp<2` (resolves to 1.29.1,
   the API the code is written against). Migrating to 2.x is separate,
   real work. Other unpinned entries (`langchain-openai`, `anthropic`,
   `pypdf`, `pyyaml`, `python-multipart`, `langchain-mcp-adapters`) are
   the same class of risk and have not bitten yet.
2. **`npm run build` fails** — 8 pre-existing TypeScript errors
   (7 × `TS7053` indexing `CSSProperties` with a `string` in the
   agents-map components, 1 × `TS2741` missing `onOpen` prop in
   `Cockpit.tsx`). This is **not** a deployment problem: `vite build`
   alone succeeds (376 modules), and `npm run dev` runs fine, because
   Vite does not typecheck. It means `tsc -b` was already broken before
   this machine existed — the workflow here is `npm run dev`, and nobody
   runs the production build. Real, but app code, not config.

**The `tools\*.cmd` launchers were broken and are now fixed.** Every one
of them hardcoded `C:\myWorx\Projects\Second Brain\...` — the *first*
machine's path, with a space — so they failed on any other checkout.
They now resolve everything from `%~dp0` (the script's own location), so
the repo can live anywhere and be renamed freely. `run-prototype.cmd`
additionally called `py -m http.server`, which cannot work on a fresh
machine (no `py` launcher, §1); it now uses the backend venv's Python.
`run-backend.cmd`/`run-frontend.cmd` also now fail with a readable
message instead of a cryptic one when the venv or `tools\node` is absent.

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
| `COMPASS_BASE_URL` | **The FULL completions URL**, ending in `/chat/completions` — see the warning below |
| `COMPASS_API_KEY` | API key for Compass (the same key Hermes uses as `HERMES_CUSTOM_API_CORE42_AI_API_KEY`) |
| `COMPASS_MODEL` | Model name Compass classification calls use |
| ~~`ANTHROPIC_API_KEY`~~ | **No longer required** (2026-09-03) — see below |
| ~~`ANTHROPIC_MODEL`~~ | **No longer required** (2026-09-03) — see below |
| `VAULT_PATH` | Absolute path to the Obsidian vault directory (copied over from the old laptop) |
| `SELF_EMAIL` | The Outlook mailbox address capture runs against |
| ~~`HERMES_MCP_SHARED_SECRET`~~ | **No longer required** (2026-09-03) — see below |

> **Three settings became optional on 2026-09-03.**
> `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` and `HERMES_MCP_SHARED_SECRET`
> now default to `""` in `app/config.py`. They were declared required with
> no defaults, so commenting them out stopped the backend booting with a
> `ValidationError` — even though nothing uses them.
>
> Verified before loosening them: the `anthropic` SDK is no longer
> imported anywhere under `app/` (agent chat moved to Hermes in the
> 2026-08-20 pivot), and the only remaining reader is
> `data_access/providers.py`, which seeds a Provider row for display — an
> empty credential just shows as unconfigured, which is accurate.
>
> **Security note on the empty shared secret.** `inbound_auth.py` compares
> the caller's header against this string, so an **empty** value *disables*
> the `/mcp/*` gate rather than closing it: a remote caller sending no
> header matches `""` and is allowed through. That is harmless today only
> because `data_access/system/tools/registry.json` registers no Tools, so
> nothing is mounted under `/mcp/*` to reach. **Set a real secret before
> registering the first Tool.**

> **The two Compass base URLs are deliberately different. Do not
> reconcile them.**
>
> | Consumer | Value | Why |
> |---|---|---|
> | **This app** (`.env` `COMPASS_BASE_URL`) | `https://api.core42.ai/v1/chat/completions` | `app/data_access/compass_client.py` POSTs to it verbatim, appending nothing |
> | **Hermes** (`config.yaml` `custom_providers[].base_url`) | `https://api.core42.ai/v1` | Hermes appends `/chat/completions` itself |
>
> Copying either into the other produces a real 404 — from a doubled path
> one way, a missing one the other. This has been paid for once already;
> see `Hermes-Provisioning/config/custom_providers.yaml`'s own header.

> **`.env` does not support inline comments — the comment becomes the
> value.** Hit for real on 2026-09-03. Writing
> `HERMES_BASE_URL=            # default http://127.0.0.1:9119`
> does not leave the setting unset; it sets it to the literal string
> `"# default http://127.0.0.1:9119"`. Confirmed live: `hermes_home_path`
> became `# default ~/AppData/Local/hermes` (so `.exists()` was `False`),
> and `cors_allowed_origins` became a single bogus origin, which silently
> breaks every frontend call with a CORS rejection rather than a clear
> error. **Leave an optional line fully commented out to get its default**
> — only uncomment when supplying a real value, and put explanatory text
> on its own line above.

`app/config.py` also has several settings that **do** have working
defaults, so they can be omitted: `HERMES_BASE_URL`
(`http://127.0.0.1:9119`, `hermes serve`'s real default port),
`HERMES_HOME_PATH` (`~/AppData/Local/hermes` — already correct on this
machine), `SECOND_BRAIN_DATA_PATH` (defaults to
`<VAULT_PATH>/.second-brain`), and `CORS_ALLOWED_ORIGINS` (the 5173/5174
Vite dev ports).

One oddity worth not re-investigating: `SELF_EMAIL` is **required** by
`app/config.py` but has zero real callers left in the app — capture moved
to Hermes. It still has to be set or the backend refuses to start.
`REQ-SB-84` tracks removing it.

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

**A restore leaves you with NO `.env` anywhere — that is by design, and the
setup wizard is the fix.** Confirmed by reading the tools, 2026-09-04:
`hermes_backup.py`'s own `_is_excluded` skips any file named `.env` (or
`.env.*`) wherever it appears, top-level and per-profile alike, because they
hold real secrets. `hermes_restore.py` never recreates one.

So a freshly restored install has every profile, every Skill and every cron
job — and not a single environment variable. Nothing resolves: no
`SECOND_BRAIN_VAULT_PATH`, no `SECOND_BRAIN_DATA_PATH`, no
`OBSIDIAN_VAULT_PATH`, no provider credentials.

This matters more than it looks, because of how Hermes scopes env files.
A profile is its OWN home — `hermes_constants` puts `HERMES_HOME` at
`<root>/profiles/<name>` in profile mode, and `env_loader.load_hermes_dotenv`
then loads exactly `<that home>/.env` with **no chaining** up to the
top-level file. There is no inheritance: the same values genuinely have to
exist in all 41 places (the home dir plus every profile), which is also why
`hermes profile create --clone` copies `.env` — a new profile would otherwise
start blind.

**Fix: re-run the setup wizard** (Settings > System > "Run setup wizard", or
`/setup`). Saving writes all four managed variables into every one of those
files in one pass, and its Hermes step now reports "Profiles agree on the
paths" so a profile left behind is visible rather than silently stale.
Provider credentials still have to be re-entered by hand — the wizard covers
Compass, but anything else Hermes authenticates against does not come back
from an archive either.

**Backup & Restore refuses: "the `hermes` CLI isn't on PATH".** Hit live
2026-09-03. The message is accurate and the refusal is correct — but the
CLI is almost certainly installed fine, and the real fault is the
**backend process's inherited environment**, not the archive or the
install.

`hermes_restore.py`'s `_validate` does `shutil.which("hermes")` and
refuses if it comes back `None`, because it needs the CLI to create any
profile the archive carries that the target doesn't already have. The
installer puts `%LOCALAPPDATA%\hermes\bin` on the **User** `PATH`, and a
process **never** picks up a `PATH` change made after it started — nor do
any children it spawns. So a backend launched from a terminal that was
already open before Hermes was installed inherits a `PATH` without the
Hermes bin dir, and the restore refuses even though `hermes --version`
works perfectly in a *new* shell.

Proved side by side, same interpreter, same machine, minutes apart:

```
stale PATH     : shutil.which('hermes') -> None
refreshed PATH : shutil.which('hermes') -> ...\hermes\bin\hermes.EXE
```

**Fix: restart the backend from a shell that can see it.** Either open a
new terminal, or refresh the current one first and relaunch:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
            [Environment]::GetEnvironmentVariable('Path','User')
tools\run-backend.cmd
```

Double-clicking `start.bat` from Explorer does **not** hit this — Explorer
already carries the current User `PATH`. It is specific to launching from
a long-lived shell (or any tool/agent session) that predates the Hermes
install. The same trap applies to anything else the backend shells out
to, so if a Hermes-dependent feature fails only when launched one
particular way, check this before suspecting the feature.

**Port already in use / backend won't start on 8001.** A previous
uvicorn `--reload` process can leave an orphaned worker holding the port.
Find the real live child process rather than trusting `netstat`'s
reported PID (which can be a dead parent):

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*uvicorn*" }
```

**Refined 2026-09-03 — that filter is not enough, confirmed live.** The
orphan was reproduced deliberately while verifying the launchers, and the
real shape is worse than the note above implies:

- The socket on 8001 was owned by **PID 30256, which had no process row
  at all** — `Get-Process` reported it dead while `Invoke-WebRequest
  http://127.0.0.1:8001/health` still returned `200`.
- The process actually serving was a `--reload` **multiprocessing fork
  child**, whose command line is:

  ```
  python.exe -c "from multiprocessing.spawn import spawn_main; spawn_main(parent_pid=30256, pipe_handle=340)" --multiprocessing-fork
  ```

  It contains neither `uvicorn` nor `app.main`, so **the `*uvicorn*`
  filter above misses it**, as does any filter on the app name.

Ask the port who owns it, then kill the live child by walking parentage —
and never trust "is the PID alive", because the dead parent keeps the
socket:

```powershell
$owner = (Get-NetTCPConnection -LocalPort 8001 -State Listen).OwningProcess
Get-CimInstance Win32_Process |
  Where-Object { $_.ProcessId -ne $PID -and
                 ($_.ProcessId -eq $owner -or $_.ParentProcessId -eq $owner) } |
  Select-Object ProcessId, ParentProcessId, CommandLine
```

The single most reliable check is not process listing at all — try to
bind the port. If `[System.Net.Sockets.TcpListener]` can `.Start()` on
8001, it is genuinely free regardless of what any listing claims.

**Two traps when writing these filters** (both hit during that session):
exclude `$PID`, or the PowerShell process running your own query matches
its own command-line text and you kill your own shell; and scope by
`hermes-agent` path before killing any `python.exe`, since the **Hermes
gateway is also a Python process** and taking it down silently stops
every cron job.

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
