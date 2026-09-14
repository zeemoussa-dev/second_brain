# Entities plugin — extracting Customer, Partner, Affiliate and Opportunity

**Date:** 2026-09-14 · **Requirement:** `REQ-SB-91` · **Architecture:** `ADR-021`, `ADR-022`
**Resolves:** `BUG-062`, `BUG-063` · **Repository:** `sb-plugins-entities`

Follows `2026-09-14-plugin-host-and-my-day-plugin.md`. Same delivery: direct, phase by
phase, each phase gated.

## Goal

The framework knows nothing about business (`ADR-021`). Entities are the largest remaining
leak: the registry in `Settings/Entities.md`, the Customer/Partner/Opportunity Templates,
Cockpit's Customer-based agent matching, and Customer/Partner folder names compiled into
data access and into framework capture Skills. After this plan an install without the
Entities plugin has no Customer concept anywhere, and one with it behaves as today.

## Operator decisions (2026-09-14)

| Question | Decision |
|---|---|
| Pending approvals, whose backend was archived on 2026-08-20 | **Removed for now** (`BUG-064`). When approvals return, kinds with their own decision (Company Review) are registered by a plugin. |
| Where the entity Skills live (`create-companies-partners`, `track-opportunities`, `new-company-discovery`, `entity-domain-extraction`, company half of `summarize-and-tag-threads`, `company_index.py`) | **Stay agent-owned in `sb-pss-agent`.** The plugin carries backend, screens and Templates; no Hermes layer in the Marketplace yet. |
| How My Day gets a customer | **Asks Entities through a service.** No Entities installed → My Day shows no customer. |

## What moves, what becomes a seam, what is deleted

Source: the read-only inventory of 2026-09-14 (every hit classified A/B/C).

**Into the plugin**
- Entities registry: `data_access/entities.py`, the Entities block of the backend
  `VaultManager`, `GET/POST/PATCH/DELETE /vault/entities`.
- Settings Entities page (`SettingsVaultEntitiesPage`, its client calls).
- Master Templates `customer`, `partner`, `opportunity`.
- Customer resolver and Cockpit enricher (today inside My Day).
- Cockpit expert selection by Customer (`moderator.match_customer_expert`,
  `match_customer_fallback_agent`), including the Section id and `<slug>-expert` convention.

**Seams the framework gains (Plugin API v2, `FRAMEWORK_API = 2`)**
1. `register_agent_matcher` — Cockpit asks plugins for experts and a fallback agent
   (`moderator`, `chat_store`, `chat_turn`). Chats that already stored a roster keep it.
2. `provide_service` / `get_service` — one plugin offers a capability to another without an
   import (My Day → `entities.customers`).
3. `register_seed_data_store` — `.sbf` export/import of a plugin's settings file
   (`artifact_export`, `artifact_import` hardcode `Settings/Entities.md` today). Older
   archives carrying that path stay importable.
4. **Templates layer** — a package's `templates/<id>/Template.json` is installed into the
   install's Templates by the Marketplace, recorded in ownership, validated on publish.
   Templates already on an install are adopted, never overwritten; uninstall stops owning
   them and leaves notes alone.
5. **People locations from Templates** — any Template with a `People` child is a place
   People live. Replaces the `Work/Customers` / `Work/Partners` scan in
   `vault_writer.find_person_note_path`.
6. **Cockpit info fields contributed by plugins** — replaces the hardcoded Customer field in
   `InboxCockpitPage`.

Version 2 removes nothing from v1, but every installed plugin is gated on the exact API, so
My Day is republished against v2 (1.2.0) in the same phase the bump lands.

**Deleted, not ported (no callers today)**
`customer_hub_linking.py`, `partner_hub_linking.py`, the retrofit functions of
`people_extraction.py`, and the Customer/Partner-only functions of `vault_writer.py`.
Each function's callers are re-checked before its deletion; `find_person_note_path` stays
until seam 5 replaces its scan.

## Phases

### Phase 1 — Delete dead entity code
Framework only, no behaviour change.
**Gate:** backend suite, core import check, empty boot, live smoke (Cockpit people chips
still resolve).

### Phase 2 — Plugin API v2 seams
Seams 1–6 in the framework, each with tests, none knowing a business concept. Customer
matching and the Entities registry keep working through the new seams while still in the
framework, so nothing changes for the operator yet. `FRAMEWORK_API = 2`; publish and install
My Day 1.2.0.
**Gate:** suite, import checks, publish dry-run of a test package with `templates/`, parity
of Cockpit roster and fallback on real chats, My Day unchanged.

### Phase 3 — Build `sb-plugins-entities` 1.0.0
Backend (registry, `entities.customers` service, Cockpit enricher and matcher, seed-data
store), screens (Entities settings page, Cockpit Customer info field), Templates (the three
masters). Publish, install from the Marketplace.
**Gate:** the plugin's own tests; parity on real data for Entities CRUD, Cockpit roster and
Customer field, People lookup, `.sbf` export/import.

### Phase 4 — My Day 1.3.0 asks Entities
My Day drops its own resolver and enricher and uses `get_service("entities.customers")`.
**Gate:** My Day parity with Entities installed; no customer and no error without it.

### Phase 5 — Remove Entities from the framework
Delete what moved; stop seeding the three masters; remove the Entities nav entry and route.
**Gate:** suite; empty boot; a grep gate for Customer/Partner/Opportunity in executable
framework code (comments and test fixtures excepted); `BUG-062` and `BUG-063` closed.

## Reported to the agent repos, not done here
- `company_index.py` leaves the framework's shared managers; `sb-pss-agent` provisioning
  must ship it before Phase 5, or its deployed company Skills break.
- Framework capture Skills (`email-thread-capture`, `meeting-capture` `vault_lib.py`,
  `capture-notes`, `capture-files`) scan `Customers/` / `Partners/` for People and
  auto-links. Moving them to Template-driven lookups is framework Skill work, tracked with
  seam 5 so moving the Templates does not create duplicate People.

## Open questions (before the phase that needs them)
1. **`summarize-and-tag-files` company tagging** (Phase 5): split the company half out to
   `sb-pss-agent`, or keep file summaries tag-free of companies? (Phase 5)
2. **Where the Entities settings page lives** (Phase 3): under Settings → Plugins (today's
   host rule), or may a plugin add a page to the Vault settings nav?
3. **Capture classifications** (`ingest_email` `internal|partner|customer`) and auto-link
   names (Phase 2/5): declared by Templates, or contributed by the plugin?
