# Architecture

Living description of Second Brain's system as it is today. Update this file as
the architecture evolves — it describes what IS, not what MIGHT BE.

**Last reviewed:** 2026-08-10

## System Overview

Second Brain indexes and serves the user's Obsidian vault (markdown notes with
frontmatter and wikilinks) directly — no staging/promotion gate, since it's the
user's own trusted personal data, not agent-written scratch data. Standalone
project; Hermes (an external MCP-based multi-channel communication tool) is a
planned integration point, not something this project builds. Future integration
with `agentic-map`'s agents is a deliberately separate, later decision.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Frontend | TypeScript + React + Vite |

## Source Layout

```
src/
  backend/    — Python + FastAPI application
  frontend/   — TypeScript + React + Vite application
```

## Data Model

[Describe the core entities and their relationships — notes, frontmatter fields,
wikilink graph, tags/index structures — once `/architect` establishes them at
`/plan-tasks`.]

## Authentication & Authorisation

[Describe the auth approach — likely none/local-only for a single-user tool, to be
confirmed at `/plan-tasks`.]

## Local Development

[Describe how to run the system locally — services to start, env vars to set
(e.g. path to the Obsidian vault directory).]

## External Services

Hermes (MCP-based multi-channel communication) — planned integration, not yet
built.
