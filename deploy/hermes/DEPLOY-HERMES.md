# Deploying Hermes to an offline server

Hermes is the **agent runtime**: it runs the scheduled jobs and the capture,
and it answers the API Second Brain reads. It is a separate product —
[NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent),
MIT licensed — with its own release folder because it has its own lifecycle.

**Install Second Brain first.** A Second Brain server without Hermes is a
complete install: every screen that would show agent activity says "not
configured" rather than looking broken. The reverse is not true — Hermes on
its own has nothing to serve.

This folder is a complete release. The server needs **no internet**: every
package, toolchain and installer is in `vendor\`. Upstream's own installer
cannot be used here; it clones from GitHub, resolves from PyPI and downloads
a Node toolchain and a browser, and has no offline mode.

Steps are marked:

- **[SCRIPT]** — a script does it. Run it and read what it prints.
- **[MANUAL]** — a person does it. A script cannot, or should not.

---

## What is in here

```
RELEASE.json                 the Hermes version and commit this was built from
DEPLOY-HERMES.md             this file
app\hermes-agent\            Hermes' source, as committed upstream, with its
                             web bundle already built
app\deploy\                  the installer, the service wrapper, the checker
vendor\python-runtime\       Hermes' own Python interpreter
vendor\wheels\               every package Hermes needs, as files
vendor\requirements-hermes.txt  what the installer installs from them
vendor\node\                 the Node toolchain
vendor\bin\uv.exe            so Hermes never tries to download it
```

**Nothing is installed machine-wide** except two services and the DLLs their
host needs. Hermes manages its own interpreter, so the release copies one in
rather than running a Python installer — and it cannot collide with the
Python Second Brain uses on the same server.

That interpreter choice is deliberate. Hermes refuses to use SQLite's WAL
mode on any SQLite below 3.51.3, and the newest python.org 3.11 installer
ships 3.45 — so a system Python would leave the gateway writing session
state through the coarsest locking SQLite has, permanently. The copied
runtime is Python 3.11.16 with SQLite 3.53.1, and the build refuses to
publish a release whose runtime does not clear that bar.

**What is deliberately absent**, and why you will not find it:

- No profiles, no sessions, no `auth.json`, no `config.yaml`, no `.env`, no
  logs, no caches, no skills. This is a clean install for a different
  account, not a copy of anyone's machine.
- No `node_modules`. Its only job is building the dashboard's web bundle,
  which is **already built** and shipped as 3 MB of output instead of 366 MB
  of input.
- No `.venv`. One built elsewhere hard-codes that machine's user path; the
  installer builds a fresh one from `vendor\wheels`.
- No `.git`. A side effect worth knowing: Hermes decides whether an update is
  available by counting commits behind `origin/main`, finds no checkout, and
  silently does nothing. On a box with no internet that is the behaviour you
  want.

---

## Before you start

1. **Windows Server**, with administrator rights.
2. **An inference endpoint and key.** Hermes calls a model for every turn.
   The endpoint is the **API root** — for Compass, `https://<host>/v1`, with
   nothing after it.
3. **Second Brain already installed**, if the two are to work together.

> **One trap, stated once.** Second Brain's `COMPASS_BASE_URL` is the **full**
> completions URL, ending in `/chat/completions`. Hermes' `base_url` is the
> **root**, without it, because Hermes appends that itself. Same endpoint,
> same key, two deliberately different values. Putting either in the other's
> place returns 404 from both.

---

## 0. Getting it onto the server — [MANUAL, then SCRIPT]

The routes onto an Azure VM with no internet — redirected RDP drive, Bastion,
Azure Files — are written up once, in the Second Brain release's `DEPLOY.md`
under *Getting the release onto the server*. The same routes carry this
folder.

Two things specific to this release:

- **Fingerprint it before it travels**, on the build machine, so a truncated
  copy is caught here rather than three steps later:

  ```powershell
  .\deploy\stage-for-transfer.ps1 -ReleasePath .\Release-Hermes
  ```

  Then, on the server, `.\verify-hermes.ps1 -Manifest` checks every file
  against it and stops. Copy with `robocopy /Z` so an interrupted transfer
  resumes.

- **Do not put `-HermesHome` on `D:`.** On an Azure VM `D:` is the ephemeral
  temp disk and is wiped when the VM is deallocated or resized. `C:\Hermes`
  (the default) or an attached data disk.

---

## 1. Install — [SCRIPT]

Copy this whole folder to the server, open **an elevated PowerShell**, and:

```powershell
cd <this folder>\app\deploy
.\install-hermes.ps1 -ModelBaseUrl https://<your model host>/v1 -ModelName <the model>
```

It checks what it needs before changing anything — elevation, the release's
own contents, that port 9119 is free — then lays down the source and Hermes'
own Python runtime, builds the virtual environment from the vendored wheels,
puts the Node toolchain and `uv` in place, writes a `config.yaml` and an
`.env`, registers two services, and fills in the two lines an installed
Second Brain needs to find it.

Defaults worth knowing:

| Flag | Default | |
|---|---|---|
| `-HermesHome` | `C:\Hermes` | everything: source, venv, config, profiles, logs |
| `-DashboardPort` | `9119` | what Second Brain expects |
| `-DashboardHost` | `127.0.0.1` | see *Reaching the dashboard* below |
| `-SecondBrainBackend` | `C:\SecondBrain\src\backend` | skipped if not there |

It is safe to run again. Every step checks whether it is already done, and a
re-run **replaces the source and leaves the home alone** — so an upgrade is
this same command with a newer release, and your profiles, sessions and
config survive it.

---

## 2. The key — [MANUAL]

Open `C:\Hermes\.env` and fill in the one blank line the installer added near
the bottom:

```
HERMES_COMPASS_API_KEY=<the key>
```

**This is manual on purpose.** The key is a credential; it is not in the
release and should not be in a script, a screen-share or a ticket.

`C:\Hermes\config.yaml` names that variable and holds no secret of its own,
so it can be read, copied and diffed freely. Check the two model lines in it
while you are there.

---

## 3. Start it — [SCRIPT]

```powershell
Start-Service HermesGateway
Start-Service HermesDashboard
.\verify-hermes.ps1
```

`verify-hermes.ps1` makes the same requests Second Brain makes: both services
are running, a key is set, the dashboard serves its page, **that page carries
a session token**, the public API answers, the token opens the authenticated
API, the gateway wrote a log, both come back after a restart, and stopping
one leaves no orphaned processes behind.

You do **not** have to run `hermes setup` first. A clean install creates its
own `default` profile on the first start — verified on a fresh one, where
`/api/profiles/active` answered `{"active":"default"}` without anyone
configuring anything.

The session-token check is the one that matters most. Second Brain holds no
Hermes credential — it reads the token out of the dashboard's own HTML and
sends it back on every call. A dashboard serving without its web bundle looks
healthy from every other angle and cannot be talked to at all.

---

## 4. Let Second Brain provision it — [MANUAL, in the browser]

Hermes is installed but it does not yet know where the vault is, or where
Second Brain's own Skills keep their shared code.

In Second Brain, open **Settings › System**, check that the Hermes fields are
filled (the installer did that), and **save**.

Saving is what provisions this Hermes: Second Brain writes the vault path,
the data root and the mailbox into Hermes' `.env` **and every profile's**,
copies the shared Skill managers into `C:\Hermes\managers`, and puts that
directory on Hermes' `PYTHONPATH`.

**Do not write those by hand.** Second Brain is the only thing that knows the
full set, and a Skill whose shared code is not on `PYTHONPATH` fails at run
time — in 2026 an install accumulated 228 stale copies of one manager across
41 profiles, every one of them silently winning over the correct version.
Second Brain re-does this on every save, which is what makes staleness
impossible.

---

## Reaching the dashboard

It binds `127.0.0.1` by default, so it is reachable **from the server only**
— over RDP, or an SSH tunnel. That is deliberate: it terminates no TLS and
authenticates with a session token, so on a company network it would be a
token travelling in clear text.

`-DashboardHost 0.0.0.0` exposes it. If you do that, put it behind something
that terminates TLS, and know that Second Brain's own interface already shows
the agent activity, the sessions and the cron jobs — most of what the
dashboard is for.

---

## Updating to a newer release

1. Build a new release on the development machine.
2. Copy it over; **stop both services**.
3. Run `install-hermes.ps1` again with the same arguments.
4. Start both services and run `verify-hermes.ps1`.

Your `config.yaml`, `.env`, profiles and sessions are left alone: a re-run
replaces the source and the virtual environment, nothing else.

---

## When something is wrong

**A service will not start.** Two places to look, in order:
`C:\Hermes\logs\service-gateway.log` (or `service-dashboard.log`) is the
child process's own output — a service has no console, so the wrapper puts it
there. Then Event Viewer → Windows Logs → Application, source
`HermesGateway` / `HermesDashboard`, where the wrapper itself reports why it
could not start at all.

**"The service did not respond in a timely fashion."** The pywin32 service
host cannot load its DLLs. The installer's `pywin32_postinstall` step does
that; re-run the installer.

**The dashboard answers but Second Brain says Hermes is unavailable.** Check
`HERMES_BASE_URL` and `HERMES_HOME_PATH` in Second Brain's `.env`, then run
`verify-hermes.ps1` — if "its page carries a session token" fails, the web
bundle is missing and the release was built wrong.

**The log says the key "is not set" — but it is.** Expect this line on every
start, and ignore it:

```
Config ref '${env:HERMES_COMPASS_API_KEY}': HERMES_COMPASS_API_KEY is not set
(check ~/.hermes/.env); keeping the literal placeholder
```

Hermes reads its config once before it loads `.env`, warns about the
reference it cannot resolve yet, and resolves it properly on every read
afterwards. Verified on a clean install: with that warning in the log,
`hermes config get model.api_key` returned the real key. If you want to be
sure on your own server, run exactly that.

**Every agent turn fails to authenticate.** Then the key really is missing or
wrong, or `base_url` in `config.yaml` has `/chat/completions` on the end. See
the trap above. `hermes config get model.api_key` tells you which.

**The first start takes half a minute.** Measured at 26 seconds on a clean
install before it answered. `verify-hermes.ps1` waits; a browser hit in the
first few seconds just fails.

**Node refuses every HTTPS call** (`UNABLE_TO_GET_ISSUER_CERT_LOCALLY`). Node
ships its own certificate list and does not know the corporate root. The
installer sets `NODE_OPTIONS=--use-system-ca` in `.env` for this; check it is
still there.

**Scheduled jobs do not run.** The *gateway* runs cron, not the dashboard.
`Get-Service HermesGateway`.

---

## What this release cannot do

Said plainly, so nobody discovers it at the wrong moment:

- **It cannot fetch anything.** Hermes normally installs provider and channel
  extras on demand, the first time one is picked. This release carries the
  full set the install it was built from had resolved; anything beyond that
  cannot be added on this server at all.
- **It cannot update itself.** `hermes update` needs a git checkout and
  GitHub. Updating means building a new release here and re-running the
  installer.
- **No browser automation.** The tools that drive a browser need a Chromium
  that an offline installer cannot download.
- **No WhatsApp channel.** Its setup runs `npm install` against a registry
  this server does not have.
- **It cannot run as a named user whose password rotates.** Both services run
  as `LocalSystem`. There is a `-ServiceAccount` flag, and on this VM you
  should not use it: the administrator password is checked out of BeyondTrust
  and rotates, so a service holding those stored credentials works until the
  next rotation and then fails somewhere else entirely. The same goes for
  anything under that account's `%LOCALAPPDATA%` — which is exactly why
  `-HermesHome` defaults to `C:\Hermes`.
