# Deploying Second Brain to an offline server

This folder is a complete release. The server it installs on needs **no
internet**: every package, toolchain and installer it uses is in `vendor\`.

Steps are marked:

- **[SCRIPT]** — a script does it. Run it and read what it prints.
- **[MANUAL]** — a person does it. A script cannot, or should not.

---

## What is in here

```
RELEASE.json          what this was built from, and when
DEPLOY.md             this file
app\                  the application: backend code, frontend source + built UI,
                      the plugins, the service wrapper and the install scripts
vendor\python\        the Python installer
vendor\wheels\        every backend package, as files
vendor\node\          the Node toolchain
vendor\node_modules.zip  the frontend's packages
```

**What is deliberately absent**, and why you will not find it:

- No vault, no config folder, no `.env`, no accounts, no chats, no certificates.
  This is a clean install for a different account, not a copy of anyone's machine.
- No `.venv`. One built elsewhere hard-codes that machine's user path and will
  not run here; the installer builds a fresh one from `vendor\wheels`.
- No tests, no `Implementation\`, no `Documentation\`, no prototype, no git
  history. The package carries the code, not the development lifecycle. To
  check the install, use `verify.ps1`, which tests the running app.

---

## Before you start

You need, on the server:

1. **Windows Server**, with administrator rights.
2. **A folder for the vault** — the Obsidian notes this install reads.
3. **A folder for this install's own state** — accounts, chats, the note index,
   installed plugins. **It must not be inside the vault.** When those were the
   same folder on 2026-09-03, every agent-side Skill silently stopped finding
   its templates.
4. **The certificate**, if serving on 443. See the next section.

---

## 1. The certificate — [MANUAL]

The app terminates TLS itself. There is no IIS or nginx in front of it: the UI
and the API are one process on one port, so there is **one certificate**, not
one for a frontend and one for a backend.

Ask whoever issues certificates for:

- a **certificate file** and its **private key**, both **PEM** (`-----BEGIN
  CERTIFICATE-----`), with the full chain in the certificate file if there is
  an intermediate;
- issued for **the name people will type in the browser** — the server's FQDN,
  not `localhost`.

If they hand you a `.pfx`, convert it on a machine that has OpenSSL:

```
openssl pkcs12 -in server.pfx -clcerts -nokeys -out server.crt
openssl pkcs12 -in server.pfx -nocerts -nodes  -out server.key
```

Put both somewhere the service account can read and **nobody else can** — not
in the install folder, which is readable by anyone who can read the app.

> **While you are waiting for a certificate** you can install with `-Port 80`
> and no certificate, then re-run `install.ps1` with the certificate and
> `-Port 443` when it arrives. Re-running is safe.

---

## 2. Install — [SCRIPT]

Copy this whole folder to the server, open **an elevated PowerShell**, and:

```powershell
cd <this folder>\app\deploy
.\install.ps1 -VaultPath D:\Vault `
              -DataRoot D:\SecondBrainData `
              -Port 443 `
              -CertificateFile C:\certs\secondbrain.crt `
              -CertificateKeyFile C:\certs\secondbrain.key
```

It checks what it needs before changing anything — elevation, the vault, that
the data root is not inside it, that the port is free, that a certificate was
given for 443 — then installs Python, builds the virtual environment from the
vendored wheels, unpacks the Node toolchain, writes `.env`, and registers the
service to start at boot and restart on failure.

It is safe to run again. Every step checks whether it is already done, so a run
that failed halfway can simply be repeated.

---

## 3. The model provider — [MANUAL]

Open `C:\SecondBrain\src\backend\.env` and fill in:

```
SELF_EMAIL=you@example.com
COMPASS_BASE_URL=https://<your Compass host>/v1/chat/completions
COMPASS_API_KEY=<the key>
COMPASS_MODEL=<the model>
```

**This is manual on purpose.** The key is a credential; it is not in the
release and should not be in a script, a screen-share or a ticket.

`COMPASS_BASE_URL` is the **full route**, ending in `/chat/completions`, not a
host. Everything except these four lines is already filled in.

> **Hermes** (the agent runtime that does capture and scheduled jobs) is
> optional and is **not** in this release — it is a separate product with its
> own installer and its own account. Leave `HERMES_BASE_URL` and
> `HERMES_HOME_PATH` blank. The app runs, and every screen that would mention
> Hermes says it is not configured rather than looking broken.

---

## 4. Start it — [SCRIPT]

```powershell
Start-Service SecondBrain
.\verify.ps1 -Port 443 -ServerName <the name on the certificate>
```

`verify.ps1` makes real requests: the service is running, `/health` answers,
the web interface is served, its JavaScript loads, a deep link reloads into the
app, the API refuses an anonymous caller, the certificate is the one you
expect, and it all comes back after a restart.

---

## 5. The first account — [MANUAL]

Browse to `https://<server>/` from a workstation. The install has no accounts,
so it offers **Create the first Admin**. Fill it in; that account is an Admin
and can create the rest in **Settings › Users**.

Until that is done, anyone who can reach the server can create that first
account. Do it now rather than later.

---

## 6. Plugins — [SCRIPT, from the browser]

The plugins are in `app\src\marketplace`. Install them from **Settings ›
Marketplace**.

Installing one **rebuilds the web interface on this server** — that is why the
Node toolchain and `node_modules` are in the release. It takes a few minutes
and the app is briefly unavailable while it happens, so do it before people
start using it.

---

## Updating to a newer release

1. Build a new release on the development machine.
2. Copy it over; **stop the service**.
3. Run `install.ps1` again with the same arguments. It leaves `.env`, the data
   root and the vault alone, and replaces the code.
4. Start the service and run `verify.ps1`.

Nothing in the release can overwrite your data: it contains none.

---

## When something is wrong

**The service will not start.** Look in Event Viewer → Windows Logs →
Application, source `SecondBrain`. The service writes why it could not start
there, because a service has nowhere else to say it.

**"Port is already held by…"** on install. On a fresh Windows Server, port 80
or 443 is usually IIS (`W3SVC`) or WinRM. Stop and disable the one that is not
yours, or install on another port.

**The page loads but every action fails.** Almost always `COMPASS_*` not filled
in, or filled in with a host instead of the full `/chat/completions` route.
`Settings › System` shows what this install thinks it has.

**The browser warns about the certificate.** The name on the certificate is not
the name being typed, or the chain is incomplete. `verify.ps1` prints the
subject it found.

**It worked, then stopped after a reboot.** `Get-Service SecondBrain` — the
installer sets it to start automatically; if someone set it to Manual, that is
the cause.

---

## What this release cannot do

Said plainly, so nobody discovers it at the wrong moment:

- **It cannot fetch anything.** A package that is not in `vendor\` cannot be
  installed on that server at all. That includes a plugin that arrives later
  with a new dependency.
- **It cannot install Hermes.** The agent runtime is a separate product.
- **The vendored wheels are built for this release's Python minor version.**
  If a different Python is already on the server and takes precedence, the
  install will fail at the package step rather than quietly building something
  that does not match.
