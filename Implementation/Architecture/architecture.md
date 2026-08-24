# Architecture

Living description of Second Brain's system as it is today. Update this file as
the architecture evolves — it describes what IS, not what MIGHT BE.

**2026-08-20:** The pre-redesign description of this system is archived,
not deleted — see `Documentation-Archive-2026-08-20/Implementation/
Architecture/architecture.md`. This file is being rewritten from scratch
alongside the backend architecture redesign ([ADR-001](ADR.md), executing
the Hermes/LangGraph pivot).

**Current status: mid-redesign, skeleton only.** The block-by-block design
work is happening collaboratively (operator + assistant as Architect/
Business Analyst) and is tracked live in `Implementation/Plans/2026-08-20-
backend-architecture-redesign.md` — that document is the actual source of
truth for the emerging shape right now, not this file. This file will be
filled in once the design stabilizes past the "empty skeleton folders"
stage; until then, treat anything written here as provisional.

## What exists today (confirmed, not aspirational)

- **Data taxonomy** (operator-defined): System Data (Second Brain's own
  operational state), Hermes/LangGraph Data (their own execution data, not
  ours to own), Vault Data (the real Obsidian vault — OKF directories/
  notes with frontmatter).
- **Data Access layer:** `app/data_access/vault/`, `app/data_access/
  system/` (with `app/data_access/system/provider/` inside it) — empty
  skeleton folders, nothing migrated in yet.
- **Business layer:** `app/business/logic/`, `app/business/vault/`,
  `app/business/core/`, `app/business/hermes/`, `app/business/langgraph/`
  — empty skeleton folders, nothing migrated in yet.
- **API layer:** confirmed to need no restructuring — stays a flat folder
  of single-purpose router files, same as before this redesign.
- The pre-redesign backend is still fully running in production
  (unaffected by the skeleton above) and is fully preserved at
  `Backend-Backup/backend-2026-08-20/` as the migration source.

See the Plans doc for open questions (the approval/safety gate, the
capture trigger's home, `core`'s exact definition, the MCP boundary's
placement) and the Provider schema still being settled.
