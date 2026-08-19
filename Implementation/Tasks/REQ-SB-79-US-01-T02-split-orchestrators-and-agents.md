---
id: REQ-SB-79-US-01-T02
title: Two new Agent identities + run_housekeeping_pass() split + 5-call-site rewire
parent_story: REQ-SB-79-US-01
requirement_id: REQ-SB-79
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-79-US-01-T02 — Two new agents + orchestrator split + call-site rewire

## Parent Story

- Story: [[REQ-SB-79-US-01]] — `../UserStories/REQ-SB-79-US-01-librarian-two-sub-pipelines.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-79 *The Librarian — Two Sub-Pipelines*
- Architecture: `Implementation/Architecture/architecture.md` → "The Librarian — Two Sub-Pipelines" §§ "Two new Agent identities", "Job → new-owning-agent mapping", "Orchestrating capability split"; `Implementation/Architecture/ADR.md` → `ADR-058` Decisions 1, 3, 4

---

## Objective

Create the two new Agent identities (`threads-cleaning`, `company-and-partner-building`) under the existing "Librarian" Section, split `run_housekeeping_pass()` into `run_threads_cleaning_pass()`/`run_company_partner_building_pass()`, and re-wire all 5 literal `agent_id="librarian-housekeeping"`-shaped references to `"company-and-partner-building"`.

---

## Starting State → End State

**Before / Inputs:**
- `librarian_housekeeping.ensure_librarian_agent_and_section()` (`Done`) idempotently creates ONE agent, `librarian-housekeeping`, under the "Librarian" Section.
- `run_housekeeping_pass()` chains all 5 Jobs: `rename_threads`, `link_thread_messages`, `backfill_files`, `populate_thread_related_links`, `backfill_company_folders`.
- 5 literal `agent_id="librarian-housekeeping"`-shaped references exist: `_create_librarian_company_link_proposal`'s own default `requesting_agent_id` parameter (line ~494), its one call site inside `backfill_company_folders` (line ~589), `propose_customer_backfill` (line ~693), `propose_company_review` (line ~849), `propose_customer_archival_candidates` (line ~1118).

**After / Outputs:**
- `ensure_librarian_agent_and_section()` is renamed/generalized to `ensure_librarian_agents_and_section()` — existence-checks and creates BOTH new agents (mirrors the existing per-agent existence-check-first shape, applied twice):

  ```python
  def ensure_librarian_agents_and_section() -> dict:
      section = section_registry.create_section("Librarian")
      results = {}
      for agent_id, name, settings in [
          ("threads-cleaning", "Threads Cleaning", [...]),
          ("company-and-partner-building", "Company and Partner Building", [...]),
      ]:
          existing = agent_registry.get_agent(agent_id)
          if existing is not None:
              results[agent_id] = {"id": agent_id, **existing}
              continue
          created = agent_registry.create_agent(name, type="worker", settings=settings)
          section_registry.set_agent_section(created["id"], section["id"])
          results[agent_id] = created
      return results
  ```

  (Exact `settings` text is a scope-internal judgement call for the coder — describe each pipeline's own real job chain/schedule, mirroring the existing `librarian-housekeeping` settings shape.)
- `run_housekeeping_pass()` is replaced by two siblings (see architecture.md's own code block, reproduced exactly):

  ```python
  def run_threads_cleaning_pass() -> dict:
      return {
          "rename_threads": rename_threads(),
          "link_thread_messages": link_thread_messages(),
          "backfill_files": backfill_files(),
          "populate_thread_related_links": populate_thread_related_links(),
      }


  def run_company_partner_building_pass() -> dict:
      return {
          "backfill_company_folders": backfill_company_folders(),
          "retrofit_people_from_emails": people_extraction.retrofit_people_from_emails(),
      }
  ```

- `librarian_housekeeping.py` gains one new import: `from app.business import people_extraction`.
- All 5 literal `agent_id="librarian-housekeeping"`-shaped references become `"company-and-partner-building"` — the exhaustive set: `_create_librarian_company_link_proposal`'s own default `requesting_agent_id` parameter; the one call site inside `backfill_company_folders`; `propose_customer_backfill`; `propose_company_review`; `propose_customer_archival_candidates`.

---

## Files to Modify

- `src/backend/app/business/pipelines/librarian_housekeeping.py` — all edits above.

---

## Constraints

- Inherits from parent story.
- **No new Section** — both new agents assign to the SAME already-existing "librarian" Section id.
- **Zero new Job logic** — `rename_threads`/`link_thread_messages`/`backfill_files`/`populate_thread_related_links`/`backfill_company_folders`/`propose_customer_backfill`/`propose_customer_archival_candidates`/`propose_company_review` are called unmodified; only their orchestrating wrapper and owning-agent identity change.
- **The rename-must-run-first ordering guarantee is preserved by construction** — `run_threads_cleaning_pass()`'s own dict-literal call order is unchanged from `run_housekeeping_pass()`'s own first 4 entries.
- **`propose_customer_backfill`/`propose_customer_archival_candidates`/`propose_company_review` stay individually, manually triggered** — never folded into `run_company_partner_building_pass()`'s own scheduled wrapper (`ADR-055`/`ADR-057`'s own "manually-triggered only" precedent, untouched).
- **All 5 call sites, the complete exhaustive set** — confirm by grep after the edit that zero `agent_id="librarian-housekeeping"`/`requesting_agent_id="librarian-housekeeping"`-shaped literal remains in this file.
- `people_extraction.retrofit_people_from_emails()` is reused verbatim — zero new mechanism (business-to-business composition, mirrors this module's own already-established horizontal-call precedent).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-79-US-01-AC-01]` Call `ensure_librarian_agents_and_section()` (fresh state, or against a disposable/reset test overlay). Confirm BOTH `threads-cleaning` and `company-and-partner-building` agent records are created, both assigned to the same "librarian" Section id. Call it a second time; confirm it is a true no-op (no duplicate/disambiguated agent created).
2. `[REQ-SB-79-US-01-AC-02]` Call `run_threads_cleaning_pass()` directly against real Thread data. Confirm all 4 Jobs run, in the same order as before, and the returned dict has exactly these 4 keys (no `backfill_company_folders`).
3. Call `run_company_partner_building_pass()` directly. Confirm the returned dict has exactly `backfill_company_folders` and `retrofit_people_from_emails` keys, and both real sub-calls actually ran (non-trivial real results, not stubs).
4. `[REQ-SB-79-US-01-AC-04]` Call `propose_customer_backfill()` (or trigger a real ambiguous mention via `backfill_company_folders()`) against real data that produces a real Pending Approval. Confirm the created record's own `agent_id` is `"company-and-partner-building"`.
5. `[REQ-SB-79-US-01-AC-05]` By direct reading of the post-edit source, confirm `propose_company_review`'s own `create_pending_approval` call site already uses `"company-and-partner-building"` — this holds regardless of whether `REQ-SB-76-US-01` has shipped yet (the function may not be callable end-to-end if `REQ-SB-76`'s own upstream logic isn't in place, but the identity re-wire is confirmed by source inspection either way).
6. Grep the post-edit file for `librarian-housekeeping`; confirm zero remaining literal `agent_id=`/`requesting_agent_id=` reference to it (comments/docstrings referencing the OLD identity for historical context are fine — only live code references matter).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `[REQ-SB-79-US-01-AC-01]` Both new agents created under the Librarian Section, idempotent on re-call
- [ ] `[REQ-SB-79-US-01-AC-02]` `run_threads_cleaning_pass()` bundles the same 4 jobs, same order
- [ ] `run_company_partner_building_pass()` bundles `backfill_company_folders` + `retrofit_people_from_emails`
- [ ] `[REQ-SB-79-US-01-AC-04]` A real Pending Approval from `propose_customer_backfill`/`propose_customer_archival_candidates` carries `agent_id="company-and-partner-building"`
- [ ] `[REQ-SB-79-US-01-AC-05]` `propose_company_review`'s own call site confirmed re-wired by source inspection
- [ ] All 5 literal `librarian-housekeeping` call sites confirmed replaced (grep-clean)
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Skill/grant/schedule registration for the two new orchestrators — `T03`/`T05`.
- `email_poc_router.py`'s own route split — `T04`.
- Retiring `librarian-housekeeping` — `T05`.
- Building `propose_company_review` itself — `REQ-SB-76-US-01`'s own scope.

---

## Context / Notes

`REQ-SB-77-US-01-T03` (a sibling story) carries a real `depends_on` edge directly onto THIS task — it cannot verify Scenario 6's own scheduled self-heal half until `run_company_partner_building_pass()` exists. Keep the function's own name and the `people_extraction.retrofit_people_from_emails()` composition exactly as specified above; do not rename or restructure it beyond this task's own scope, since `REQ-SB-77-US-01-T03` depends on this literal shape.

---

## Implementation Log

**Change:** `src/backend/app/business/pipelines/librarian_housekeeping.py` —
added `from app.business import ... people_extraction ...` import;
`ensure_librarian_agent_and_section()` replaced by `ensure_librarian_
agents_and_section()` (creates/existence-checks both `threads-cleaning`/
`company-and-partner-building`, both assigned to the same "librarian"
Section); `run_housekeeping_pass()` replaced by `run_threads_cleaning_
pass()`/`run_company_partner_building_pass()` exactly per the architecture's
own code block; all 5 literal `agent_id="librarian-housekeeping"`/
`requesting_agent_id="librarian-housekeeping"` references rewired to
`"company-and-partner-building"` (`_create_librarian_company_link_
proposal`'s own default param + its one call site, `propose_customer_
backfill`, `propose_company_review`, `propose_customer_archival_
candidates`). Also corrected one stale docstring reference in `propose_
company_review` ("never wired into `run_housekeeping_pass()`" →
"...`run_company_partner_building_pass()`") for accuracy — comment-only,
in-scope (same file, same task).

**Verification methodology (disclosed):** the real vault has 141 real
Threads; one real `detect_mentioned_companies` Compass call measured
~25.6s. `populate_thread_related_links`/`backfill_company_folders` each
call this once per Thread with NO bounding parameter (existing,
unmodified job behavior — "Zero new Job logic" forbids adding one) — a
full-corpus direct call would cost ~2 hours of real Compass round-trips
for T02 alone, before T04/T06 would need to repeat it. Per this project's
own established Learnings precedent (`SPRINT-028`: "Bound a live-data
verification to a real, filtered subset via in-process monkeypatch of the
real fetch function, rather than re-running a full real capture for every
single check"), verification below monkeypatches `vault_writer.list_
thread_notes` to dynamically re-filter (by real `conversation_id`, re-
resolved fresh on every call — NOT a frozen path list, since `rename_
threads()` mutates directory names mid-pass) down to 3 real Threads for
the general checks and 2 real `customer: "Unsorted"` real Threads for the
AC-04 check — genuine real files, real Compass calls, real writes, just
bounded in count. The corpus-wide behavior of each individual Job was
already proven at full scale in `REQ-SB-72/73/74`'s own locked ACs; this
story only needed to prove the SPLIT introduces no regression.

**Live verification (worktree's own real backend context, real
`VAULT_PATH`):**

- `[REQ-SB-79-US-01-AC-01]` `ensure_librarian_agents_and_section()` called
  twice: both `threads-cleaning`/`company-and-partner-building` created
  under the "librarian" Section on the first call; the second call
  returned the same two agents with no `-2`-suffixed disambiguated
  duplicate anywhere in `list_agents(include_retired=True)`. **PASS.**
- `[REQ-SB-79-US-01-AC-02]` `run_threads_cleaning_pass()` (bounded, real)
  returned exactly `{"rename_threads", "link_thread_messages",
  "backfill_files", "populate_thread_related_links"}` — no `backfill_
  company_folders` key. Same fixed job order preserved (dict-literal
  order unchanged from the pre-split code). **PASS.**
- `run_company_partner_building_pass()` (bounded, real) returned exactly
  `{"backfill_company_folders", "retrofit_people_from_emails"}`; both
  sub-calls produced real, non-trivial results — `backfill_company_
  folders` created 4 real Customer folders (2 new pending-approval-
  bypassing `new_unambiguous` classifications) and 2 real Pending
  Approvals for `ambiguous` mentions; `retrofit_people_from_emails`
  processed all 696 real vault notes (not bounded — this Job scans the
  whole vault by design, unaffected by the Thread-count monkeypatch).
  **PASS.**
- `[REQ-SB-79-US-01-AC-04]` `propose_customer_backfill()` (bounded to 2
  real `Unsorted` Threads) created ONE real batched Pending Approval
  (`76e6718db8dc`). Independently confirmed via `pending_approval_
  registry.get_pending_approval` (a fresh, separate read, not trusting
  the create-call's own return value alone) that all 3 real Pending
  Approvals created this pass (`1326a80c3f57`, `a05bf0b903ec` from
  `backfill_company_folders`; `76e6718db8dc` from `propose_customer_
  backfill`) carry `agent_id == "company-and-partner-building"`. **PASS.**
- `[REQ-SB-79-US-01-AC-05]` `inspect.getsource(propose_company_review)`
  confirms its own `create_pending_approval` call site already reads
  `agent_id="company-and-partner-building"` — true regardless of
  `REQ-SB-76-US-01`'s own ship status. **PASS.**
- Grep of the post-edit file for `agent_id="librarian-housekeeping"`/
  `requesting_agent_id="librarian-housekeeping"` — zero matches (only 4
  harmless comment/docstring mentions of the OLD identity remain, for
  historical framing). **PASS.**

**Real, disclosed side effects on the live vault from this bounded
verification (transparency, not bulk-processing — nothing was approved/
declined, only created, mirroring the Job's own real, intended,
already-`Done` behavior):** 4 new real Customer folders created
(Innovation and Digital Development Agency (IDDA), Ministry of Digital
Development and Transport (MDDT), AzInTelecom LLC, AZCON Holding); 3 new
real Pending Approvals left `pending` for the operator's own review; 1
real Thread routed from `Unsorted` to Ministry of Digital Development and
Transport (MDDT); `## Related` regenerated on 3 real bounded Threads. All
of this is the SAME real mechanism `REQ-SB-72/74` already ship — this
task only changed WHICH agent identity owns the resulting record.

gate: clear 2026-08-19 — no MUST-FLAG trigger fired. Bounded-verification
methodology is a disclosed, scope-internal judgement call (not a locked-AC
weakening — every AC's own real mechanism/outcome was directly, genuinely
observed), logged here for human spot-check.
