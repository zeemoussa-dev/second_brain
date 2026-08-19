# Second Brain

A personal knowledge base service that indexes and serves an Obsidian vault
directly — no staging or promotion gate, because the vault is already
trusted personal data, not agent-written scratch data.

Second Brain parses and indexes your vault's markdown notes (frontmatter,
wikilinks, tags), lets you browse and search them, and runs a set of
autonomous agents that capture email, meetings, and tasks from Outlook,
classify them, and file them into the vault as living notes. A planned
integration point (Hermes, an MCP-based multi-channel communication tool)
will let the same agents be reached from outside the app.

## Stack

- **Backend** — Python + FastAPI (`src/backend`): vault parsing/indexing,
  Outlook COM capture, agent orchestration (LangGraph), Compass/Anthropic
  LLM integration, MCP tool server.
- **Frontend** — TypeScript + React + Vite (`src/frontend`): Agents Map,
  My Day dashboard, notes browser/search, agent chat.
- **Design authority** — `html-prototype/` is a clickable, no-build-step
  HTML/CSS/JS prototype. It is the source of truth for any screen it
  covers; open `html-prototype/index.html` directly in a browser.

## Quick start (Windows 11)

1. Copy `src/backend/.env.example` to `src/backend/.env` and fill in the
   required values (see [Documentation/DeploymentGuide.md](Documentation/DeploymentGuide.md)
   for what each one means).
2. Double-click **[`start.bat`](start.bat)** at the repo root. It opens the
   backend and frontend dev servers each in their own window and prints
   the URLs to open.

   Or start them individually:

   ```bash
   tools\run-backend.cmd    # FastAPI on http://localhost:8001
   tools\run-frontend.cmd   # Vite on http://localhost:5173
   tools\run-prototype.cmd  # static prototype on http://localhost:8088
   ```

Full prerequisites, port list, and troubleshooting live in
[Documentation/DeploymentGuide.md](Documentation/DeploymentGuide.md).

## Project layout

| Path | What it is |
|---|---|
| `src/backend` | FastAPI backend — vault indexing, KB API, Outlook capture, agents |
| `src/frontend` | React + Vite frontend |
| `html-prototype/` | Clickable design-authority prototype, no build step |
| `Documentation/PRD.md` | Full product requirements |
| `Implementation/` | Delivery pipeline: user stories, tasks, sprints, architecture/ADRs |
| `BACKLOG.md` | Index of every requirement and the story that implements it |
| `MEMORY.md` | Append-only log of standing decisions, patterns, constraints |
| `CHANGELOG.md` | Entry for everything created |

## How this project is built

Second Brain is built through a multi-agent delivery pipeline
(analyst → architect → decomposer → product-owner → coder) driven by
slash commands (`/spec`, `/plan-tasks`, `/plan-sprints`,
`/implement-sprint`). See
[Implementation/Pipeline.md](Implementation/Pipeline.md) for the full
contract before touching any of that tooling.

## Status

Check [REVIEW-QUEUE.md](REVIEW-QUEUE.md) for items awaiting a human
decision, [BACKLOG.md](BACKLOG.md) for requirement coverage, and
[Implementation/Sprints/](Implementation/Sprints/) for what's shipped.
