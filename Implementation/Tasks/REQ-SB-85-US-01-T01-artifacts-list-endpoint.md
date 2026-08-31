---
id: REQ-SB-85-US-01-T01
title: app/business/logic/artifacts_inventory.py + GET /artifacts — cross-type artifact listing
parent_story: REQ-SB-85-US-01
requirement_id: REQ-SB-85
type: backend
status: Done
gate: clear
gate_reason: "clear 2026-08-31 — no MUST-FLAG trigger fired; both locked ACs (AC-01, AC-03) verified live against the real deployment"
phase: P2
depends_on: []
created: 2026-08-31
updated: 2026-08-31
---

# REQ-SB-85-US-01-T01 — app/business/logic/artifacts_inventory.py + GET /artifacts: cross-type artifact listing

## Parent Story

- Story: [[REQ-SB-85-US-01]] — `../UserStories/REQ-SB-85-US-01-artifact-browser.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-85 *Artifact Export/Import — Portable Capability Bundles (`.sbf`)*

---

## Objective

Compose the four already-`Done` Managers (`SkillManager`/`TemplateManager`/
`AgentManager`/`PipelineManager`) into one tagged, cross-type artifact
list, exposed as `GET /artifacts` — pure read composition, zero new
store, zero write path.

---

## Starting State → End State

**Before / Inputs:**
- `SkillManager().get_all()`, `TemplateManager().get_all()`,
  `AgentManager().get_all()`, `PipelineManager().get_all()` each already
  return that entity's own real dataclass list — confirmed live, all four
  `Done` (`REQ-SB-80`). No cross-type composition module exists yet.
  `app/api/artifacts_router.py` does not exist yet.

**After / Outputs:**
- `app/business/logic/artifacts_inventory.py` (new) exposes
  `list_all_artifacts() -> list[dict]` — one flat list, each entry
  `{"kind": "skill"|"template"|"agent"|"pipeline", "id": str, "name": str,
  "description": str}`. `kind` is always exactly one of the 4 literal
  strings (no 5th value ever produced — `US-02`/`US-03`'s own manifest
  `kind` field and this endpoint's `kind` field are the same vocabulary,
  by construction, since both name the same 4 real entity kinds).
  `name`/`description` are pulled from each entity's own real field
  (Skill.name/description; Agent.name/description; Pipeline.name/
  description; Template — confirmed by direct reading of the `Template`
  dataclass that no `name`/`description` field exists today — so `name`
  falls back to `template.id` and `description` falls back to
  `template.note_name or ""`, never fabricated). A malformed Template
  (`Template.error` set, per `TemplateManager.get_all()`'s own honest-list
  convention) is still included in the list, with `description` set to
  `f"Error: {template.error}"` instead of silently dropped.
- `app/api/artifacts_router.py` (new) — `GET /artifacts` returns
  `list_all_artifacts()` directly, the same flat single-purpose-router,
  thin-wrapper convention every other entity uses
  (`pipelines_router.py`/`sections_router.py`).
- `app/main.py` — imports and registers `artifacts_router`, same
  `app.include_router(...)` pattern as every other router.

---

## Files to Modify

- `src/backend/app/business/logic/artifacts_inventory.py` (new file).
- `src/backend/app/api/artifacts_router.py` (new file).
- `src/backend/app/main.py` — import + `app.include_router(artifacts_router)`.

---

## Constraints

- Inherits from parent story.
- **Pure read composition — no owned store, no write path.** Never a 5th
  "Manager"; lives in `business/logic/` alongside `section_agents.py`/
  `cockpit_view.py`/`system_health.py`, the established cross-entity,
  no-owned-store pattern (architecture `§Artifact Inventory Composition`).
- **Exactly the 4 kinds the PRD names** — Skill, Template, Agent,
  Pipeline. No Provider/Section/Vault-Index kind is added.
- Recompute fresh on every call — no caching (matches `system_health.py`'s
  own "recompute fresh, no caching" convention; the list must always
  reflect the real, current deployment, per `AC-01`).
- Never import `app.hermes` directly — reach Hermes-backed data only
  through the already-real `SkillManager`/`AgentManager` (which
  themselves go through `app.business.hermes.client.get_client()`).

---

## Tests

<!-- Every locked AC from the parent story must appear as at least one numbered
verification step here, prefixed with its AC-ID in square brackets. -->

**Manual verification steps:**
1. `[REQ-SB-85-US-01-AC-01]` Call `list_all_artifacts()` directly (or
   `GET /artifacts` via `TestClient`) against the real, current
   deployment; confirm the response contains a real entry for every
   `SkillManager().get_all()`/`TemplateManager().get_all()`/
   `AgentManager().get_all()`/`PipelineManager().get_all()` id, each with
   the correct `kind` literal, and that the counts per kind match each
   Manager's own real `len(get_all())` exactly (no fabricated/stale
   entries, no dropped ones).
2. `[REQ-SB-85-US-01-AC-03]` Confirm a kind with zero real artifacts on
   this deployment (if one currently exists, e.g. no real Pipelines yet)
   contributes zero entries of that `kind` to the flat list, without
   raising or omitting the other 3 kinds' own real entries (no AC-tagged
   UI assertion here — the honest-empty-state RENDERING is `T02`'s own
   observable behaviour; this step confirms the backend data shape that
   makes it possible: an honestly empty subset, not a crash or a
   fabricated placeholder row).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `list_all_artifacts()` returns one real, correctly-`kind`-tagged
      entry per real Skill/Template/Agent/Pipeline, sourced only from the
      4 already-`Done` Managers
- [x] `GET /artifacts` returns this list, registered in `main.py`
- [x] A malformed Template is still listed (never silently dropped)
- [x] No caching — a call made after a real underlying change reflects it
      immediately
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Multi-select UI, selection state, the Settings landing-page card — `T02`.
- Export/Import themselves — `REQ-SB-85-US-02`/`US-03`.
- Any create/edit/delete of any artifact — untouched, existing (or
  future) surfaces own that.

---

## Context / Notes

Architecture `§Artifact Inventory Composition` (`REQ-SB-85-US-01`),
`Implementation/Architecture/architecture.md`, is the authoritative design
for this task — read it before starting. No ADR needed for this task —
the architect pass confirmed this section composes only already-Accepted
Manager gateways.

---

## Implementation Log

**Built (2026-08-31):**
- `app/business/logic/artifacts_inventory.py` (new) — `list_all_artifacts()`
  composes `SkillManager().get_all()` / `TemplateManager().get_all()` /
  `AgentManager().get_all()` / `PipelineManager().get_all()` into one flat
  list of `{"kind", "id", "name", "description"}` dicts. No module-level
  cache/state — each call re-invokes all 4 real `get_all()`s fresh.
- `app/api/artifacts_router.py` (new) — `GET /artifacts` thin wrapper,
  same shape as `system_health_router.py`/`pipelines_router.py`.
- `app/main.py` — `artifacts_router` imported + registered via
  `app.include_router(...)`, same pattern/position as every sibling
  router.

**Scope-internal judgement call (logged for human spot-check, not an
escalation):** `Agent.description` is typed `str | None` on the real
`Agent` dataclass, but the task's own End-State locks the response
schema's `description` field to `str`. Coerced `agent.description or ""`
for the `agent` kind only (mirrors the already-spec'd Template fallback
for the same "never `None` on the wire" reason) — no other field on any
of the 4 dataclasses needed this.

**Verification — manual mode, real deployment, no test tooling yet:**

- `[REQ-SB-85-US-01-AC-01]` **PASS.** Ran `GET /artifacts` via
  `fastapi.testclient.TestClient(app)` (instantiated directly, not as a
  context manager, so the app's own heavy `lifespan` — Registry boot,
  vault reindex — never fires; a real HTTP round trip through the real,
  unmodified `app` object all the same) against the real, current
  deployment. Response: `200`, 70 total entries (`skill=17`,
  `template=10`, `agent=40`, `pipeline=3`). Independently cross-checked
  by calling each of the 4 real Managers' own `get_all()` directly (no
  API layer) in the same script and diffing id-sets + counts per kind
  against the response: all 4 kinds matched exactly (`ids_match=True`,
  `real_count == resp_count` for every kind) — no fabricated/stale
  entries, none dropped. Every `kind` value in the response was one of
  the 4 literal strings (`{'skill','template','agent','pipeline'} `
  superset check passed).
- `[REQ-SB-85-US-01-AC-03]` **PASS**, with one disclosed real-data
  limitation and a substitute technique used to still genuinely prove
  it. The real, current deployment has zero kinds at 0 count today
  (`skill=17`/`template=10`/`agent=40`/`pipeline=3`) — the task's own
  Tests step is itself conditional ("if one currently exists"). Induced
  the real zero-artifact condition via a scoped, reverted in-process
  monkeypatch of the real, already-loaded `PipelineManager.get_all`
  (returns `[]` for the duration of one call only), then called the real
  `list_all_artifacts()` directly: `pipeline` entries = 0, while
  `skill`/`template`/`agent` stayed at their real 17/10/40 (unaffected,
  not raised, not omitted) — no crash, no fabricated placeholder row.
  Reverted the monkeypatch and re-called `list_all_artifacts()`
  immediately after: real pipeline count returned to 3, confirming the
  patch was properly scoped/reverted, not a permanent change, and
  incidentally reconfirming the DoD's "no caching" checkbox (the very
  next call after a real underlying change reflects it immediately, both
  directions).

**Additional check beyond the Tests block's own named steps (the
"malformed Template still listed" DoD checkbox, not itself a locked
AC-ID for this task):** the real deployment currently has zero malformed
Templates (`TemplateManager().get_all()` returned none with `.error`
set). Induced one honestly via the same scoped-monkeypatch technique —
`TemplateManager.get_all` patched to append one real `Template(id=
"__induced_malformed__", note_name=None, error="Expecting value: line 1
column 1 (char 0)")` (the exact dataclass shape `TemplateManager.get_all()`
itself produces for a genuinely unparsable `Template.json`) alongside the
real, unmodified other 10 real Templates, then reverted. Result: 11
template entries, the induced one present with
`description == "Error: Expecting value: line 1 column 1 (char 0)"` —
confirms `artifacts_inventory._template_entry()`'s malformed-Template
branch is real and reachable, not dead code.

No `ESCALATIONS.md` / `REVIEW-QUEUE.md` entries — no MUST-FLAG trigger
fired. No new `MEMORY.md` entry — this task followed the already-`Done`
`business/logic/` cross-entity composition precedent
(`system_health.py`) and `TemplateManager.get_all()`'s own
already-documented malformed-Template convention directly; nothing new
to record.

gate: clear 2026-08-31 — no MUST-FLAG trigger fired (no ADR
created/changed, no unresolved assumption, both locked ACs verified
live against real data with one disclosed, honestly-substituted
technique for the two conditions the real deployment doesn't currently
exhibit on its own).
