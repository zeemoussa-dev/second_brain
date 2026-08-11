# MEMORY

Append-only log of decisions, patterns, and constraints discovered during delivery.
Updated by Claude when a task produces a new rule or constraint worth preserving
across sessions.

**Protocol (from CLAUDE.md):**
- Decisions → `## Decisions` — format: `[date] Decision – Reason`
- Patterns → `## Patterns` — format: `Pattern name – description`
- Constraints → `## Constraints` — format: `Constraint – reason`
- Do NOT add logs, chat transcripts, or debugging output.

---

## Decisions

- [2026-08-11] People (REQ-SB-10) are flat notes at `Work/People/<Person>.md`
  with Company as a `company/<slug>` tag — never a folder, and a separate
  namespace from `customer/<slug>` (a person's employer isn't always a
  customer account; many real contacts are internal Core42 colleagues or
  third parties). Same reasoning as ADR-004's customer-as-tag decision.
  Backfilled from already-captured Email notes' sender fields (deduped by
  email address); the Meeting-based half is real but blocked on REQ-SB-08
  not existing yet. Full schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`.
- [2026-08-10] Reversed the earlier "Drop" call on agentic-map's REQ-079/
  080/081 (pipeline_items/customer_entitlements tables + tools) – real
  captured email data confirmed Second Brain's actual customer domain is
  Azure MACC/consumption business (ADNOC/TAQA/Masdar/Core42), exactly what
  those requirements were built for in agentic-map. Reshaped for notes
  instead of DB rows: `Work/Pipeline/`, `Work/Agreements/`, `Work/
  Consumption/` (one note per snapshot, atomic) plus a `Work/Customers/`
  hub note per customer. Full schema:
  `Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`. Structure
  only — no ingestion/agent code for these yet.
- [2026-08-10] Adopted *Beyond the Second Brain* (Mo Elkholy) as a standing
  architecture reference – the operator supplied the book (`Documentation/
  References/beyond-the-second-brain-methodology.md` is the condensed
  summary); read it before making vault-structure or AI-integration
  decisions. It surfaced real tensions with what the email-classification
  POC had already shipped (folder-heavy structure, no AI-output review
  gate, non-atomic notes) — flagged in that file, not silently reconciled;
  awaiting an operator decision on how much of the method to adopt.
- [2026-08-10] No staging/promotion gate on ingested vault data – Second Brain
  indexes the user's own trusted Obsidian vault, not agent-written scratch data;
  the two-tier staging→canonical model `agentic-map` uses (its invariant 4) does
  not apply here and is intentionally not replicated.
- [2026-08-10] Standalone project, no agentic-map integration built yet – future
  integration (agentic-map's agents querying this KB) is a deliberately separate,
  later decision, not part of this project's initial scope.
- [2026-08-10] Second Brain's PRD requirements (REQ-SB-01..06) were seeded by
  walking agentic-map's 76-entry REQUIREMENTS.md and classifying each as
  Port/Adapt/Drop/Already-covered – the overwhelming majority dropped (sales
  pipeline, Outlook/mail, the agent-routing console, multi-agent orchestration
  are all out of scope). Full classification and reasoning:
  `Implementation/Plans/2026-08-10-agentic-map-requirement-port.md`.
- [2026-08-10] Agents may write to the vault (REQ-SB-04) and content may enter
  the vault via a non-Obsidian ingestion path (REQ-SB-05) – both were open
  product questions, resolved permissively by the operator rather than
  defaulting to read-only/Obsidian-only. Scope/confirmation rules for writes
  are deferred to `/spec` time, not decided here.
- [2026-08-10] Email-classification POC validated end-to-end (Outlook COM →
  Compass classify-by-customer → vault note write) against a real inbox –
  confirms the Hermes-skill-wrapping approach from the earlier Outlook
  integration-sourcing constraint is workable. Code lives at
  `src/backend/app/{data_access/outlook_com.py,data_access/compass_client.py,
  data_access/vault_writer.py,business/email_classification.py}`, exposed at
  `POST /poc/classify-emails`.
- [2026-08-10] Resolved the *Beyond the Second Brain* tension above,
  partially – (a) no AI Staging/review gate for now (classification
  accuracy spot-checked as good this session; revisit if real
  misclassifications show up), (b) folder-vs-links restructuring started
  immediately: `Work/Customers/<Customer>/<Kind>/` flattened to
  `Work/<Kind>/`, customer demoted from folder level to frontmatter + tag
  only. Not fully reconciled — atomic notes and output-orientation are
  still open.

## Patterns

- Both `list_known_customers` and `list_known_kinds` in `app/data_access/
  vault_writer.py` derive their lists from the vault itself (frontmatter
  scan / folder scan respectively) — never hardcode a customer or kind
  list in business logic. This replaced an earlier `_KNOWN_CUSTOMERS`
  hardcoded placeholder in `email_classification.py`, since removed.

## Constraints

- Hermes's own internal architecture (not Second Brain's to build or track,
  per the dependency constraint just below): agents are categorized by Type
  (`Expert`, `Worker`, `Hub`, more to come) and belong to a Section/
  Department; LLM access is multi-provider (currently Compass backed by
  GPT-5, with Compass+GPT-OSS and Anthropic planned). Recorded 2026-08-10
  as context only — if a future requirement needs Second Brain to track
  which agent/section/provider handled something, that's new scope, not
  implied by this note.
- Hermes (external MCP-based multi-channel communication tool) is an integration
  point, not something this project builds — treat it as a dependency with its own
  interface, not code to implement here.
- Hermes integration-sourcing precedence: for any external system Second Brain
  needs to reach (starting with Outlook mail/calendar), prefer a native Hermes
  skill or MCP server if one already exists; otherwise wrap an existing working
  implementation as a Hermes skill rather than building fresh. Concretely for
  Outlook — no Graph API (company-blocked, no Azure AD app registration
  possible) — wrap agentic-map's existing `outlook_com` skill (COM automation
  against locally-running desktop Outlook; see agentic-map's ADR-0018) as a
  Hermes skill, don't reimplement it. Same single-laptop-with-Outlook-desktop-
  running constraint carries over.
- No admin rights on the development host – both backend and frontend toolchains
  must be usable without a system installer. Python runs via the `py` launcher
  (3.14.6 is what's actually present, not 3.12 as originally assumed — see
  ADR-001); Node.js is a portable zip extracted to `tools/node/`, never a system
  install (see ADR-002).
- Vault note filenames must never be built from date+subject alone — two
  Outlook items can share both (a resend, a duplicate share notification),
  and a plain `date-subject.md` scheme silently overwrites one with the
  other. Always include a uniqueness slice (e.g. the source EntryID) in the
  filename stem. Found live in the email-classification POC 2026-08-10,
  fixed in `app/business/email_classification.py`.
- Known data-quality wrinkle (not yet fixed): the `type`/`kind` value for
  regular email notes is inconsistently `"email"` (singular, from an earlier
  Compass response) vs `"Emails"` (plural, current) across existing notes —
  same wrinkle shows up in their `kind/email` vs `kind/emails` tags. Harmless
  today (both are valid, dynamically-discovered kinds) but will read as two
  different kinds until reconciled; don't silently merge them without the
  operator's say-so, since agentic-map's own precedent for this kind of
  taxonomy drift is a real, judged decision, not a mechanical fix.
- Backend code must respect the `api → business → data_access` layer boundary
  (ADR-003) — a router calling `data_access` directly, or `business` doing its
  own filesystem/HTTP I/O, is a scope violation, not a style nitpick.
- The vault has two top-level roots, `Personal/` and `Work/` — everything
  Second Brain writes (email classification and onward) goes under `Work/`,
  never `Personal/`. Concretely: `email_classification.py` writes to
  `Work/<Kind>/` (e.g. `Work/Emails/`), not `Personal/...`.
- Customer is never a folder level — only frontmatter (`customer:`) and a
  `customer/<slug>` tag. Per *Beyond the Second Brain*'s "folders are the
  enemy of thinking," an email's customer relevance is multidimensional and
  shouldn't force one physical location; reclassifying is a tag edit, not a
  file move. `Kind` (Emails/Files/Notifications/...) remains a folder level
  since it's a genuinely stable, single-home property of a note.
- Since `REQ-SB-07-US-01-T04` wired `capture_scheduler.lifespan` into
  `app/main.py`'s `FastAPI(...)`, **every backend dev-server start/restart
  fires a real capture run** (live Outlook fetch → Compass classify → vault
  write) via the unconditional app-start trigger — `uvicorn --reload`
  triggers this on every reload, not just the first start. Do not restart
  the dev server repeatedly while working in `src/backend` without
  expecting real side effects (Outlook COM calls, Compass API calls, and
  vault writes against the live `.env`-configured vault).
- **Standing design rule (operator directive, 2026-08-11): every note-type
  schema must define both tags AND wikilinks, always** — never ship a
  schema with one but not the other. Tags alone (no links) leave Obsidian's
  graph view showing disconnected dots, exactly the bug REQ-SB-14 fixed for
  Customer-tagged content; links alone (no tags) lose tag-pane/search
  discoverability independent of physical location. This is a mandatory
  design-time checklist item for every future note type (People, Meetings,
  Industry, and anything after), not a one-off fix — check both before
  calling a schema resolved. Applied immediately to People (see the
  Decisions entry above): Person notes wikilink to their Company's Customer
  hub note when the company matches an existing customer (reusing
  REQ-SB-14's existing hub-note mechanism, no new concept introduced); when
  the company isn't a known customer, there is no hub note yet to link to,
  so the tag alone stands honestly until one exists — that is a real
  absence of a link target, not an overlooked link.
