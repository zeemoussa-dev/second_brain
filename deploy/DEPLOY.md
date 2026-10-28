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
TRANSFER.sha256       a hash of every file, to prove the copy arrived whole
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

### On an Azure VM, two of these have a wrong answer that looks right

**Never put the vault or the data root on `D:`.** On an Azure Windows VM `D:`
is the *temporary* disk. Windows labels it "Temporary Storage" and it is
emptied when the VM is deallocated, resized, or moved to another host — so the
vault and every account, chat and index would disappear on a stop/start, with
nothing broken to point at. **Put them on `C:`**, which is the OS disk and is
persistent, or on an attached managed data disk if the VM has one. `Get-Disk`
tells you: if it lists only the OS disk and a temporary disk, there is no data
disk, and `C:` is the right answer rather than a compromise — the whole
install, with the release staged beside it, is under 10 GB against the 127 GB
an Azure OS disk usually has.

**The network security group needs an inbound rule for your port** (443, or
80) from the range your workstation sits in. Without it the service runs, the
server answers itself, and the page never loads from anywhere else — which
reads exactly like an application fault.

### If the administrator password comes from a password manager

Where the local administrator password is checked out from a vault such as
BeyondTrust Password Safe, **it rotates**. Nothing on this server may run *as*
that account: a service or scheduled task holding its password works until the
next rotation and then fails somewhere unrelated. This install avoids that by
default — the service runs as `LocalSystem`, Python installs for all users,
and the data root is a path you choose rather than anything under a user
profile. The one way to undo it is to pass `-ServiceAccount` with a managed
login, so don't.

---

## 0. Getting the release onto the server — [MANUAL], then [SCRIPT]

A server with no internet cannot fetch this folder, so it has to be pushed.
**No internet is not the same as no network**: the routes below all use the
internal network or Azure's own backbone, and one of them will be open.

Run these three on the server, in an administrator PowerShell, and take the
first that answers. Each test is one line, and knowing which route exists
before moving gigabytes is worth the minute.

**1. A file share you can both see** — the simplest, and in a corporate VNet
usually already there.

```powershell
net view \\<file-server>            # or: Test-NetConnection <file-server> -Port 445
```

If it answers, copy the release to that share from here and pull it down there
with the robocopy below. No Azure changes, nothing to provision.

**2. A redirected drive in your remote-desktop session.**

```powershell
dir \\tsclient\
```

If your local drives are listed, copy straight from them. If the path does not
exist, redirection is stripped — which is what a vaulted, recorded privileged
session normally does — and no `mstsc` setting will bring it back. Where you
connect through **Azure Bastion**, the portal's browser session cannot
transfer files at all, but the **native client** (`az network bastion rdp`)
can: it needs the Standard SKU and Azure CLI 2.62 or newer.

**3. Azure Files, on a private endpoint in the VM's own VNet.** This is the
one to provision if neither of the above answers, and it is worth doing
anyway — every future update uses it too. A private endpoint keeps the traffic
on Azure's backbone, so it is not "internet" and commonly survives the policy
that blocked everything else.

```powershell
net use Z: \\<account>.file.core.windows.net\<share> /user:Azure\<account> <key>
```

`net use` is built into Windows, which is the point: `azcopy` would itself
have to be transferred before it could transfer anything. It needs outbound
445 to the endpoint's private address — `Test-NetConnection
<account>.file.core.windows.net -Port 445` says whether you have it.

**Then copy, with `robocopy` rather than Explorer:**

```powershell
robocopy <source> C:\Staging\Release /E /Z /R:2 /W:5
```

`/Z` is restartable mode. Any of these channels can drop, and resuming beats
starting a multi-gigabyte copy over.

### Or as one file, which over a share is better

8,000 files over a share is 8,000 round trips and a virus scan each. The build
machine can hand you a single archive instead, with
`stage-for-transfer.ps1 -SingleArchive`: a `Release.tar.gz` and a
`Release.tar.gz.sha256`. Carry both, then on the server:

```powershell
# 1. did the one file survive the copy
(Get-FileHash .\Release.tar.gz).Hash -eq (Get-Content .\Release.tar.gz.sha256).Split(' ')[0]
# 2. unpack
mkdir C:\Staging -Force; tar -xzf .\Release.tar.gz -C C:\Staging
# 3. and check every unpacked file
cd C:\Staging\Release\app\deploy; .\verify.ps1 -Manifest
```

`tar` is in `C:\Windows\System32` on Server 2019 and later, so nothing has to
be installed to unpack this. **Unpack somewhere short, and `C:\Staging` is the
reason this file says `C:\Staging` everywhere.** The deepest file in the
release is 137 characters of relative path, which from `C:\Staging\` lands at
about 148 against Windows' limit of 260 — so a staging folder more than a
hundred characters deep will fail part-way through, file by file, and the
install then fails later for reasons that have nothing to do with the install.

**Then check the copy arrived whole — [SCRIPT]:**

```powershell
cd C:\Staging\Release\app\deploy
.\verify.ps1 -Manifest
```

This compares every file against `TRANSFER.sha256`. Do it **before**
installing. A transfer that truncates a wheel does not report it; the install
succeeds, and the failure surfaces days later as a package that cannot be
imported, on a machine you cannot debug from. If anything is reported, run the
same robocopy again — with `/Z` it resumes — and check again.

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

With the folder copied and checked (step 0), open **an elevated PowerShell**:

```powershell
cd <this folder>\app\deploy
.\install.ps1 -VaultPath C:\Vault `
              -DataRoot C:\SecondBrainData `
              -Port 443 `
              -CertificateFile C:\certs\secondbrain.crt `
              -CertificateKeyFile C:\certs\secondbrain.key
```

`C:` is deliberate: it is the only persistent disk on an Azure VM that has no
data disk attached. **Do not use `D:`** — see "Before you start". If a managed
data disk is attached, use its letter instead.

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
> optional and is **not** in this release — it is a separate product with a
> release folder of its own, `Release-Hermes`, and its own runbook
> (`DEPLOY-HERMES.md`). Leave `HERMES_BASE_URL` and `HERMES_HOME_PATH` blank
> here: installing Hermes fills them in, and until then the app runs with
> every screen that would mention Hermes saying it is not configured rather
> than looking broken.
>
> **Install Second Brain first**, then Hermes. A Second Brain server without
> Hermes is a complete install; Hermes on its own has nothing to serve.

---

## 4. Start it — [SCRIPT]

```powershell
Start-Service SecondBrain
.\verify.ps1 -Port 443 -ServerName <the name on the certificate>
```

A first start is not instant — it reads the vault and builds its index before
it serves anything — so `verify.ps1` waits up to 180 seconds for `/health`
rather than asking once and calling a starting server a broken one. Raise it
with `-StartupTimeoutSeconds` for a very large vault.

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

**It answers on the server but not from your desk.** `verify.ps1` passing
locally and the page never loading elsewhere is a network rule, not the app:
the NSG (and the server's own firewall) needs the port opened inbound. Check
from the server with `Get-NetFirewallRule`, and in the portal for the NSG.

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
- **It cannot install Hermes.** The agent runtime is a separate product, with
  its own release folder and runbook.
- **It cannot open a port to the outside.** The server's firewall and, on
  Azure, the network security group are changed where they live, not from
  here. The installer refuses to start on a port something else already holds,
  but it cannot make a port reachable.
- **It cannot get itself onto the server.** Step 0 is a person with a remote
  desktop session or a file share. Nothing in here can pull itself across.
- **The vendored wheels are built for this release's Python minor version.**
  If a different Python is already on the server and takes precedence, the
  install will fail at the package step rather than quietly building something
  that does not match.
