# Deployment Guide

Second Brain runs as two local dev servers (FastAPI backend + Vite
frontend) plus an optional static prototype server. There is no hosted/
cloud deployment target today — this guide covers running it on the
Windows 11 machine that hosts the Obsidian vault and has Outlook installed.

## Prerequisites

- **Windows 11**, PowerShell 7+.
- **Outlook desktop client** installed and signed in to the mailbox named
  in `SELF_EMAIL`. Email/meeting/task capture uses Outlook COM automation
  (`pywin32`) — it drives the real, running Outlook application, not an
  API. Outlook must be installed on this machine; a Microsoft 365 web-only
  account will not work.
- **An Obsidian vault directory** the backend will read from and write to
  directly — there is no staging/promotion gate, so point `VAULT_PATH` at
  a vault you're comfortable with the agents writing into.
- **Python and Node are already provisioned in-repo** — the backend's
  `.venv` lives at `src/backend/.venv`, and a portable Node toolchain
  lives at `tools/node`. Nothing needs to be installed globally; the
  launch scripts under `tools/` reference these directly by path.

## Configuration

Copy `src/backend/.env.example` to `src/backend/.env` and fill in every
value — `app/config.py` fails to start if any are missing:

| Variable | What it's for |
|---|---|
| `COMPASS_BASE_URL` | Base URL of the Compass LLM endpoint (email/task/meeting classification) |
| `COMPASS_API_KEY` | API key for Compass |
| `COMPASS_MODEL` | Model name Compass classification calls use |
| `ANTHROPIC_API_KEY` | Anthropic API key — powers real conversational agent chat (LangGraph) and any agent using the Anthropic Provider |
| `ANTHROPIC_MODEL` | Anthropic model name |
| `VAULT_PATH` | Absolute path to the Obsidian vault the backend indexes and writes to |
| `SELF_EMAIL` | The Outlook mailbox address capture runs against |
| `HERMES_MCP_SHARED_SECRET` | Shared secret gating the `/mcp` write-capable tool endpoint (see `app/api/mcp_auth.py`) |

`.env` is gitignored — never commit it. Only `.env.example` (with empty
values) is tracked.

## Starting the app

**One click:** double-click `start.bat` at the repo root. It opens the
backend and frontend each in their own console window (so closing the
Claude/terminal session doesn't kill them) and prints the URLs.

**Individually**, from the repo root:

```bash
tools\run-backend.cmd     # uvicorn --reload, http://localhost:8001
tools\run-frontend.cmd    # vite dev server, http://localhost:5173
tools\run-prototype.cmd   # python -m http.server, http://localhost:8088
```

`.claude/launch.json` wires the same three commands into Claude Code's
own preview tooling for in-session browser verification.

## Ports

| Port | Service |
|---|---|
| 8001 | Backend (FastAPI/uvicorn) |
| 5173 | Frontend (Vite dev server) |
| 8088 | Static HTML prototype (design authority, no build step) |

## What starts automatically

The backend's FastAPI lifespan (`app/main.py`) kicks off an app-start
capture catch-up and schedules hourly recurring capture (APScheduler) the
moment `run-backend.cmd` starts — there is no separate "enable capture"
step. If Outlook isn't reachable, capture logs a failure and the server
keeps running (`app/data_access/outlook_com.py::check_reachable`); it does
not block startup.

## Building the frontend for a non-dev run

```bash
cd src/frontend
..\..\tools\node\npm.cmd run build      # tsc -b && vite build -> dist/
..\..\tools\node\npm.cmd run preview    # serves the built dist/
```

There is currently no equivalent "production" mode for the backend —
`run-backend.cmd` always passes `--reload`, which is fine for a
single-user local deployment but will restart on every file save. Drop
`--reload` from the uvicorn command if that's undesirable for a longer
running session.

## Troubleshooting

**Port already in use / backend won't start on 8001.** A previous uvicorn
`--reload` process can leave an orphaned worker holding the port even
after its parent console window is closed. The PID reported by
`netstat`/`Get-NetTCPConnection` is sometimes the *original* parent, which
may no longer exist in the process table — find the real live child
instead:

```powershell
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*uvicorn*" }
```

Kill the specific PID that command surfaces, then retry.

**Backend fails immediately on startup with a Pydantic validation
error.** A required `.env` value is missing — `app/config.py`'s
`Settings` has no defaults, by design, so a missing key fails loudly at
startup rather than silently degrading.

**Email/meeting/task capture finds nothing, or errors reaching
Outlook.** Confirm Outlook is actually running and signed in to
`SELF_EMAIL`'s mailbox on this machine — COM automation talks to the live
desktop application, not a background service.
