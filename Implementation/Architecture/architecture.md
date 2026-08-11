# Architecture

Living description of Second Brain's system as it is today. Update this file as
the architecture evolves — it describes what IS, not what MIGHT BE.

**Last reviewed:** 2026-08-11 (REQ-SB-14 vault-graph-connectivity + REQ-SB-15 manual-entry-templates pass)

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
| Backend | Python 3.14 + FastAPI (see [ADR-001](ADR.md)) |
| Frontend | TypeScript + React + Vite, portable Node.js toolchain (see [ADR-002](ADR.md)) |
| Scheduling | APScheduler (`AsyncIOScheduler`), in-process, wired into FastAPI's `lifespan` (see [ADR-005](ADR.md)) |

## Source Layout

```
src/
  backend/
    .venv/            — Python 3.14 virtual environment (not committed)
    app/
      api/             — FastAPI routers; HTTP-only, delegates to business/
      business/        — domain logic and orchestration; no HTTP, no direct filesystem access
      data_access/     — reads/writes the Obsidian vault (and any other storage); no business rules
      scheduling/      — in-process recurring/catch-up scheduler (APScheduler); a trigger
                          source parallel to api/, calls into business/ only, never
                          data_access/ directly (see ADR-005)
      main.py          — FastAPI app instantiation, router wiring, scheduler lifespan wiring
    tests/
    requirements.txt
  frontend/            — TypeScript + React + Vite application (scaffolded via `create-vite`)
tools/
  node/                — portable Node.js runtime + npm (not committed; see ADR-002)
  use-node.ps1         — dot-source to put tools/node on PATH for a shell session
```

Layer boundary (see [ADR-003](ADR.md)): `api` → `business` → `data_access`, one
direction only. A router must not reach into `data_access` directly, and
`business` must not perform HTTP or filesystem I/O of its own. `scheduling/`
(see [ADR-005](ADR.md)) is a second trigger source structurally parallel to
`api/`: it translates timer/lifecycle events (app startup, hourly interval,
in-process missed-run catch-up) into calls against `business/`, under the same
"never reach `data_access/` directly" rule — it does not sit *below* `api/` in
the request path, it sits *beside* it as an alternative entry point into
`business/`.

`app/business/customer_hub_linking.py` (REQ-SB-14, new) is the shared "ensure
the customer's hub note exists, then link this note to it" orchestration, used
by both the one-time retrofit and the going-forward capture-pipeline hook —
the same one-module-per-maintenance-operation shape as the existing
`tag_backfill.py` / `vault_restructure.py` modules already in `app/business/`.
See Data Model → "Customer Hub Notes & Graph Linking", below, for the full
layering breakdown.

## Data Model

The vault has three top-level roots: `Personal/` (untouched by Second Brain),
`Work/` (everything Second Brain's backend writes lands here — see
[MEMORY.md](../../MEMORY.md)), and `Templates/` (Obsidian core-Templates-plugin
template files — human-authored vault content, not backend-written; see
[ADR-006](ADR.md) / REQ-SB-15, below). Vault structure and note-writing conventions
follow *Beyond the Second Brain* (Mo Elkholy), adopted as a standing
architecture reference — see `Documentation/References/beyond-the-second-
brain-methodology.md` for the full summary and `ADR-004` for the concrete
folder-vs-tag decision it drove. Current state, not full adoption:

- **Folder level:** `Kind` only — `Work/<Kind>/` (`Emails`, `Files`,
  `Notifications`, and any new kind Compass proposes; see `list_known_kinds`
  in `app/data_access/vault_writer.py`). No `Customer` folder level.
- **Frontmatter, per note:** `type` (= kind), `customer`, `tags`
  (`customer/<slug>`, `kind/<slug>`), `classification_confidence`, plus
  source metadata (`subject`, `sender`, `sender_email`, `received`,
  `outlook_entry_id`, `conversation_id`).
- **Linking:** same-thread notes (matched on Outlook `conversation_id`) get
  a `## Related Emails` section with `[[wikilinks]]` to prior notes in the
  thread — Obsidian computes the reverse link automatically, so only the
  newer note needs to link forward. No reference/conceptual/tension link
  taxonomy yet (the book's Chapter 6 distinction) — everything so far is a
  reference-style link.
- **Attachments:** real (non-inline) files saved to `<subfolder>/
  attachments/<note-slug>/`, linked from the note body. Inline signature/
  logo images are filtered at capture time, never saved (`app/data_access/
  outlook_com.py`'s `_is_inline_attachment`).
- **Filename convention:** `<date>-<subject>-<entry-id-suffix>.md` — the
  EntryID suffix is required (same-subject/same-day items collide without
  it; see `MEMORY.md`).

### Customer Hub Notes & Graph Linking (REQ-SB-14)

- **Hub note per customer:** `Work/Customers/<Customer>.md` — `Customers` is a
  `kind` folder like any other (`Work/Emails/`, `Work/Files/`, ...), holding
  one `Customer`-type note per customer/affiliate; not a reversal of ADR-004
  (`customer` still never becomes a folder level for *content* classification
  — this folder holds the hub notes themselves, not customer-classified
  email/file content). Schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- **Wikilink placement — inline body, not frontmatter.** Every customer-tagged
  note gets a single line near the top of its body, e.g.
  `**Customer:** [[ADNOC]]`, linking to its hub note — extending the existing
  inline-body-wikilink convention already used for same-thread email linking
  (`## Related Emails`, above) rather than introducing a frontmatter-property
  link. Frontmatter-resolved wikilinks are a newer, version-dependent Obsidian
  behaviour; inline body links have always reliably driven the graph view,
  matching this project's established durable-over-clever preference
  (ADR-001, ADR-002). This is a direct extension of the linking convention
  already documented above, not a new structural boundary — no ADR.
- **"Ensure hub note exists, then link" logic lives in
  `app/business/customer_hub_linking.py`** (new module — see Source Layout,
  above), following ADR-003's layering and the existing `tag_backfill.py` /
  `vault_restructure.py` precedent of a dedicated business module per
  maintenance operation:
  - `app/data_access/vault_writer.py` gains the file-I/O primitives (hub-note
    path resolution, existence check, baseline-frontmatter creation reusing
    `write_note`, and a surgical "insert this body line if not already
    present" helper mirroring `insert_tags_line`'s "surgical insert, not full
    rewrite" precedent) — it does the actual reading/writing, no business
    rules.
  - `app/business/customer_hub_linking.py` orchestrates "ensure the hub note
    exists, then link this note to it" as one reusable operation, called from
    two places: the one-time retrofit (batch, over every existing
    customer-tagged note) and `email_classification.py`'s per-write hook
    (going forward) — the same shared mechanism the story requires, not two
    parallel implementations.
  - The retrofit is exposed as a new one-off endpoint,
    `POST /poc/retrofit-customer-hub-links`, in `app/api/email_poc_router.py`
    — matching the existing `/poc/backfill-tags` and
    `/poc/flatten-customer-folders` one-off-migration-endpoint precedent.
- **Preserving manually-added hub-note content (REQ-SB-10 pattern, extended).**
  "Baseline fields" are concretely the hub note's frontmatter keys only —
  `type`, `customer`, `tags`, `affiliate_of` — never its body. On first
  creation, `write_note` writes the full baseline (frontmatter + a short
  auto-generated body stub inviting the user to add their own overview). On
  every later touch (retrofit rerun, or a new note for that customer
  captured), the hub note is **never** rewritten wholesale again: each
  baseline frontmatter key is inserted only if missing (mirroring
  `insert_tags_line`'s surgical-line-insert precedent, generalized to "insert
  this line if this key is absent"), and `affiliate_of` is only ever written
  when absent — never reset to `""` once a real value exists. The body is
  never programmatically touched past initial creation, so user-added
  overview/contacts/focus content is preserved absolutely, not merely
  diffed-and-merged.

### Vault Content Conventions — Templates & In-Vault Guide (REQ-SB-15)

- **A third top-level vault root, `Templates/`** (sibling to `Personal/` and
  `Work/` — see [ADR-006](ADR.md)), holding exactly the four Obsidian
  core-Templates-plugin template files (`Templates/Customer.md`,
  `Templates/Opportunity.md`, `Templates/Agreement.md`,
  `Templates/Consumption-Snapshot.md`), each pre-filling its resolved schema
  from `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`
  field-for-field, plus the customer wikilink placement convention above.
  Configuring Obsidian's Settings → Templates → "Template folder location" to
  point at `Templates/` is a one-time manual step in the user's own Obsidian
  install — not code, not automated or tracked by `src/backend`.
- **The in-vault guide note lives at `Work/Guides/Manual-Entry-Guide.md`** —
  a new, dynamically-discoverable `kind` folder under the existing
  `Work/<Kind>/` convention (`list_known_kinds` already scans folder names, no
  code change needed for it to be found) — deliberately **not** inside
  `Templates/`, since Obsidian's Templates feature lists every file in the
  configured template folder as insertable; a guide note living there would
  wrongly appear in the "Insert Template" picker. See [ADR-006](ADR.md).
- This entire story is vault-content authoring — four template files and one
  guide note, written directly into the real vault at `VAULT_PATH` — not
  `src/backend`/`src/frontend` code; no source-layout or tech-stack change
  results from it.

**Explicitly not yet adopted** from the book (tracked as open questions, not
silent gaps): atomic notes (today's notes are full raw captures, not
one-idea distillations), output-oriented structure (organized around
`Customer`, an input entity, not around what gets produced from the vault),
and the AI Staging review gate for AI-generated classification (deferred by
the operator 2026-08-10 — direct-write stands until real misclassifications
justify revisiting it).

## Authentication & Authorisation

[Describe the auth approach — likely none/local-only for a single-user tool, to be
confirmed at `/plan-tasks`.]

## Local Development

Backend (from `src/backend`):

```
.venv\Scripts\pip.exe install -r requirements.txt   # first time / after changes
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
.venv\Scripts\python.exe -m pytest -q
```

Frontend (from `src/frontend`, after dot-sourcing `tools/use-node.ps1` once per
shell session so `npm`/`npx` resolve to the portable toolchain):

```
. ..\..\tools\use-node.ps1
npm install     # first time / after dependency changes
npm run dev
```

No admin rights are available on the development host, so neither toolchain is
system-installed — see [ADR-001](ADR.md) and [ADR-002](ADR.md).

**Scheduler runs automatically with the app (see [ADR-005](ADR.md)):** once
`app/scheduling/` is wired into `app/main.py`'s `lifespan`, every
`uvicorn app.main:app --reload` start (including each dev-server reload) fires
one real capture run immediately, then continues on an hourly interval for as
long as that process stays up. This hits the real Outlook/Compass integration
the same way `POST /poc/classify-emails` already does — be aware of this when
restarting the dev server repeatedly during REQ-SB-07 work.

Vault path / other runtime settings are not yet configurable — to be added as
a requirement when the vault-indexing story needs them.

## External Services

Hermes (MCP-based multi-channel communication) — planned integration, not yet
built.
