---
id: REQ-SB-82-US-03-T01
title: Moderator matching — customer-match and domain-match tracks
parent_story: REQ-SB-82-US-03
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: "no MUST-FLAG trigger fired at the coder pass — see Implementation Log for the two disclosed scope-internal judgement calls (dual customer-signal lookup, keyword-overlap stopword list)"
phase: P2
depends_on: []
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-03-T01 — Moderator matching — customer-match and domain-match tracks

## Parent Story

- Story: [[REQ-SB-82-US-03]] — `../UserStories/REQ-SB-82-US-03-meeting-moderator-roster-pre-assembly.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Build the two independent, purely deterministic matching functions
(`ADR-009`) that recommend a Customer Expert and/or domain Expert(s) for a
meeting/email subject.

---

## Starting State → End State

**Before / Inputs:**
- No moderator/recommendation module exists.
- Real Customer Experts (`masdar-expert`, `adnoc-expert`, `taqa-expert`, per `REQ-SB-83` — real deployed code, no story of its own) are already registered in `agents_map_adapter.py`'s `_AGENT_SECTION` under `"Customer"`.
- Real domain Experts (`azure-expert`, `macc-expert`, etc.) are already registered as `type: "expert"` and addressable via `GET /agents`.

**After / Outputs:**
- New `app/business/cockpit/moderator.py`:
  - `match_customer_expert(subject_note_stem: str) -> str | None` — reads the subject note's own `customer` tag/folder (via `vault_indexing`), maps it to a real, already-registered `<customer>-expert` agent id if one exists; `None` if not (never fabricated).
  - `match_domain_experts(subject_note_stem: str) -> list[str]` — lightweight keyword overlap between the subject's own tags/subject text and every real `type: "expert"` agent's `name`/`description` (via `agents_map_adapter.list_agent_summaries()`); returns every matching agent id, `[]` if none.

---

## Files to Modify

- `src/backend/app/business/cockpit/moderator.py` (new file)

---

## Constraints

- Inherits from parent story.
- Both functions are purely deterministic/mechanical — no LLM call, no Hermes profile involvement.
- Both tracks run and are exposed independently — this module never suppresses one track in favor of the other; combining them into one recommendation list is `T02`'s job, not this one.
- Never fabricate a match — `None`/`[]` is the honest result when nothing real matches.
- The customer-match track only maps to agent ids that are ACTUALLY registered as `Customer`-Section experts today (`masdar-expert`/`adnoc-expert`/`taqa-expert`) — never invent a `<customer>-expert` id for a customer with no real registered Expert.
- The exact keyword-overlap algorithm for `match_domain_experts` is left to your own reasonable implementation (operator's own explicit "refine later if too coarse" framing, `ADR-009`) — a plain tokenized substring/word-overlap comparison is sufficient for v1, no new per-agent schema field.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-03-AC-01] Call `match_customer_expert` on a real or scratch note tagged/foldered for "Masdar". Expect `"masdar-expert"` returned.
2. [REQ-SB-82-US-03-AC-02] Call `match_domain_experts` on a real or scratch note whose tags/subject mention "Azure". Expect the list includes a real Azure-family expert id (e.g. `"azure-expert"`).
3. [REQ-SB-82-US-03-AC-04] Call both functions on a note matching neither track (an unrelated customer/topic). Expect `match_customer_expert` returns `None` and `match_domain_experts` returns `[]` — no fabricated result.
4. [REQ-SB-82-US-03-AC-07] Call `match_customer_expert` on a note tagged/foldered for a customer with NO real registered Expert (any customer beyond Masdar/Adnoc/TAQA). Expect `None`.

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `match_customer_expert`/`match_domain_experts` implemented per Constraints
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Persisting/caching the computed recommendation (`T02`).
- Any frontend rendering (`T03`).
- Building `REQ-SB-83`'s own Customer Experts (already real, deployed).

---

## Context / Notes

`ADR-009` is the authoritative design reference. **Real dependency, not
encodable as a `depends_on` task edge:** the customer-match track's real
target agents (`masdar-expert`/`adnoc-expert`/`taqa-expert`) come from
`REQ-SB-83`, which has no story or task of its own (real, deployed code,
"Built directly this same session" — see this story's own Context and the
Notes section on `REQ-SB-83`'s no-story shape). Confirm those three agent
ids are real and registered before writing this task's own verification
steps.

---

## Implementation Log

**Built:** `src/backend/app/business/cockpit/moderator.py` (new file, only
file in `## Files to Modify`) — `match_customer_expert`/
`match_domain_experts`, both purely deterministic per Constraints. No
other file touched.

**Real research done before writing code (no scratch-note shortcut
needed):** read `agents_map_adapter.py`, `vault_indexing.py`,
`email_classification.py`/`meeting_classification.py`/
`customer_hub_linking.py`/`vault_writer.py` (`list_known_customers`,
`build_meeting_tags`, `tag_slug`) to find the REAL, current customer/tag
conventions, then inspected real notes directly under the configured
`VAULT_PATH` (`<OPERATOR_VAULT_OLD>`) and the real installed
Hermes profiles (`profile.yaml` descriptions for
`azure-expert`/`macc-expert`/`masdar-expert`/`adnoc-expert`/`taqa-expert`/
`compass-*`/`research-agent`) to ground the implementation and the
verification steps below in real data, per this project's own "compose
around the REAL current file/data, never a stale sample" precedent.

**Scope-internal judgement calls (logged for spot-check, per hard rule
5 — neither is a MUST-FLAG trigger):**
1. **Dual customer-signal lookup.** `_subject_customer()` checks BOTH
   `frontmatter.get("customer")` (Meeting notes' own baseline shape) AND a
   `customer/<slug>` tag (the ONLY signal present on real Thread/
   RawMessage notes, confirmed live — e.g. `2026-08-19 1531 Compass Access
   for Masdar` has no `customer:` key at all). Relying on either signal
   alone would silently miss real notes. See `MEMORY.md` for the full
   finding.
2. **"Customer tag/folder" read as tag+frontmatter, never a literal
   folder check.** `email_classification.py`'s own module docstring
   confirms customer is never a folder for any subject note kind this
   Cockpit serves — only `kind` is. No folder-based lookup was built.
3. **Keyword-overlap stopword list.** A plain word-overlap comparison
   against real agent `name`/`description` text produced a real, live
   false positive (an unrelated payroll-note subject matched
   `azure-services-expert` purely via the shared generic word "details")
   before `_OVERLAP_STOPWORDS` was added — the stopword list was built by
   scanning the real, current mirrored-agent vocabulary directly, not
   guessed. Disclosed in `MEMORY.md` as likely needing to grow as the real
   agent roster grows (`ADR-009`'s own "refine later if too coarse"
   framing).

**Verification — manual mode, real backend/vault/agents, no mocks.**
Ran directly against the real index (`vault_indexing.rebuild_index()`
against the real `VAULT_PATH`) and the real, installed Hermes agent
roster (`agents_map_adapter.list_agent_summaries()`), via
`.venv/Scripts/python.exe -c "..."` (backend-layer-first, no server
needed — matches this task's own `n/a` automated-tests note and this
project's own established "skip the HTTP layer when it isn't load-bearing
for the locked ACs" precedent).

- **[REQ-SB-82-US-03-AC-01]** `match_customer_expert` on two REAL vault
  notes (no scratch note needed): `2026-08-05 ADNOC Account Plan Review &
  Discussion Session - H2 FY26` (real Thread note, tag `customer/adnoc`)
  → returned `"adnoc-expert"`; `2026-08-19 1531 Compass Access for Masdar`
  (real RawMessage note, tag `customer/masdar`, no `customer:` frontmatter
  key at all) → returned `"masdar-expert"`. **PASS** — both real,
  independent customer signals resolved to the real, correct registered
  Expert.
- **[REQ-SB-82-US-03-AC-02]** `match_domain_experts` on the real Meeting
  note `2026-08-25 Azure Foundation` (subject text contains "Azure", no
  Azure-related tag) → returned `['azure-calculator',
  'azure-data-architect', 'azure-enterprise-architect', 'azure-expert',
  'azure-infra-architect', 'azure-services-expert', 'macc-expert']`.
  **PASS** — includes `azure-expert`, the AC's own named example.
- **[REQ-SB-82-US-03-AC-04]** Both functions on the real Thread note
  `2026-08-13 Naima Bikbi wants to access 'Mahmoud @ G42'` (tag
  `engagement/internal` only, subject/tag tokens confirmed to have zero
  overlap with the real agent-description vocabulary before selecting
  this note) → `match_customer_expert` returned `None`,
  `match_domain_experts` returned `[]`. **PASS** — no fabricated match on
  either track.
- **[REQ-SB-82-US-03-AC-07]** `match_customer_expert` on the real Thread
  note `2026-07-30 Aldar proposal` (tag `customer/aldar` — confirmed live,
  no `aldar-expert` profile directory exists under the real Hermes
  install) → returned `None`. **PASS.**
- **Additional, beyond the named steps:** a full-vault scan of all 492
  real notes carrying any customer signal (frontmatter or tag) confirmed
  the computed candidate agent id is always either one of the 3 real,
  live Customer-Section agent ids (`adnoc-expert`/`masdar-expert`/
  `taqa-expert`) or `None` — never a fabricated id outside that real,
  live list. Also confirmed `match_customer_expert`/`match_domain_experts`
  return `None`/`[]` (not an error) for a `subject_note_stem` absent from
  the index.

All 4 locked ACs mapped to this task verified PASS against real data. No
`ESCALATIONS.md`/`REVIEW-QUEUE.md` entry needed — no MUST-FLAG trigger
fired (no new dependency, no shared-interface change, no ADR deviation
beyond the already-flagged `ADR-009` itself, no unanticipated file; the
two items above are ordinary scope-internal judgement calls, not
escalations).

gate: clear 2026-08-25 — no MUST-FLAG trigger fired at the coder pass.
