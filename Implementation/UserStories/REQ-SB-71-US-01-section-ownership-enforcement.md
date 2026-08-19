---
id: REQ-SB-71-US-01
title: Section-Ownership Enforcement — code-enforced, per-caller allow-list on vault_writer.replace_body_section
requirement_ids: [REQ-SB-71]
requirement_section: "REQ-SB-71: Redesigned Email & Meeting Capture — Raw/Distilled Split, Section-Ownership Enforcement, People Auto-Extraction, File Companion Notes (point 6)"
phase: P1
status: Done
gate: flagged
gate_reason: "trigger-3 (ADR-048 created) — architect pass, 2026-08-18. Analyst's own gate: clear reasoning below is unaffected/preserved; the flag is the architect's own, added on top, per Implementation/Pipeline.md's ADR trigger. See ## Notes. [Coder, 2026-08-18: T01+T02 Done, all ACs verified against the real vault — see each task's own Implementation Log. finalize_background_amendment_proposal's own live end-to-end trigger was unreachable this session (disclosed, with compensating evidence, in T02's log). This flag stays open for the human's own pending ADR-048 review; not this role's to clear.]"
sprint: "SPRINT-060"
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-71-US-01 — Section-Ownership Enforcement — code-enforced, per-caller allow-list on vault_writer.replace_body_section

## Story

**As a** Second Brain operator
**I want** `vault_writer.replace_body_section` to check, in code, a real
allow-list of which body-section headers each specific caller is permitted
to write, and reject outright any call that names a header outside that
caller's own allow-list
**So that** a human-owned section — my own Personal Notes, my own Actions —
can never be silently overwritten by ANY agent regeneration pass, in ANY
note kind, anywhere in the vault, now or in the future, no matter which
pipeline calls this primitive next

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-71*, point 6 ("Section-ownership
  enforcement is a cross-cutting, foundational rule — not specific to
  Threads/Meetings, and not optional"). Raised 2026-08-18, same
  vault-structure conversation as `REQ-SB-70`/the rest of `REQ-SB-71`.
  Operator's own words, quoted directly in the PRD: *"What Challenges me is
  the Personal Info on the Item Being Re Written... It Applies everywhere
  not just on the Threads."* And, on scope: *"1 and 2 is enough"* —
  explicitly declining a heavier four-rule version (a snapshot-before-write
  safety net, or an extra approval gate beyond what `REQ-SB-57`'s
  `Background`-amendment flow already has) in favor of exactly two rules:
  ownership-typing every section, plus a code-level guard.
- **Real code read directly to ground this story, not assumed:**
  `vault_writer.replace_body_section(path, header, new_content)`
  (`app/data_access/vault_writer.py`, line 1548, `ADR-042` point 2) is
  today's ONLY "regenerate, don't patch" full-region body-rewrite
  primitive — it locates `header` by a literal, whole-line regex match and
  replaces everything between it and the next `## `-level header (or EOF),
  and it has **zero caller-awareness today**: any caller can pass any
  header string and it will replace that region unconditionally, with no
  rejection path at all. Its own docstring documents only a no-op-if-absent
  contract, nothing about who is allowed to call it with what. Confirmed by
  direct repo-wide search, `replace_body_section` has exactly **4 real call
  sites today**, all of which regenerate an agent-owned section:
  - `email_classification.py::thread_match_merge` → Thread's `## Summary`
    (`REQ-SB-67-US-01`)
  - `email_classification.py::_build_thread_related_wikilinks`'s own
    caller → Thread's `## Related` (`REQ-SB-69-US-01-T08`)
  - `thread_summary_backfill.py` → Thread's `## Summary` (one-time backfill,
    `REQ-SB-67-US-01`)
  - `project_customer_synthesizer.py` → Customer/Project `## Glimpse` (twice,
    create + resync) and `## Background` (`REQ-SB-57-US-01`)
  None of these four call sites declares any identity today, and nothing
  stops any one of them from being passed a DIFFERENT header string by a
  future bug or a careless edit — e.g. nothing today would stop a future
  change to `thread_match_merge` from accidentally calling `replace_body_
  section(path, "## Personal Notes", ...)`. This is the exact, real,
  currently-unguarded risk the operator named.
- **Why this is its own story, not folded into the Email or Meeting
  story — full reasoning, since the batch this story is part of explicitly
  asked for this decision to be made deliberately, not mechanically:**
  1. **The PRD's own words scope this as cross-cutting infrastructure, not
     a Thread/Meeting feature.** Point 6 explicitly reads "not specific to
     Threads/Meetings... Every body section in the ENTIRE vault, every note
     kind" — it is framed as a vault-wide safety rule, and its own
     Acceptance text names exactly ONE test, independent of any pipeline:
     "An agent function attempting to call `replace_body_section` on a
     section outside its own declared allow-list is rejected."
  2. **It is independently, completely testable using the four call sites
     that ALREADY exist today** — proving the guard works does not require
     `REQ-SB-71-US-02`'s (Email) or `-US-03`'s (Meeting) own new code to
     exist first. Building it standalone lets it ship and be verified in
     complete isolation, then be consumed by both.
  3. **Both `REQ-SB-71-US-02` and `-US-03` need it for the SAME reason, not
     for reasons that make one a natural "owner" of the mechanism.** Thread's
     new distilled layer (`## Summary` agent-owned, `## Personal Notes`/
     `## Actions` human-owned) and Meeting's new distilled layer (`## Summary`/
     `## History` agent-owned, `## Personal Notes`/`## Actions` human-owned)
     are structurally identical asks of the SAME mechanism. Folding the
     mechanism into whichever story happens to touch it first (Email, since
     Thread's raw/distilled split is the first concrete need) would make
     the Meeting story's own dependency on it read as "depends on Email,"
     for a reason that has nothing to do with Thread↔Meeting linking — the
     one dependency between those two stories that genuinely IS meaningful
     (Meeting's recurring-occurrence synthesis reads a linked Thread's own
     new shape, see `REQ-SB-71-US-03`'s own `## Dependencies`). Keeping this
     mechanism as its own root keeps that dependency graph honest: both
     `-US-02` and `-US-03` depend on `-US-01` for the SAME, correctly-named
     reason, and depend on each other only for the one thing that's
     actually true between them.
  4. **Sizing.** `REQ-SB-71-US-02` already carries three real, substantial
     pieces of work of its own (the raw/distilled Thread split, the
     two-stage capture pipeline, and the Files/OKF-companion convention,
     see that story's own `## Notes`) — folding a vault-wide safety
     mechanism on top risks that story growing oversized (mirrors
     `REQ-SB-69-US-01`'s own sizing-comparison reasoning, kept under
     `~8` tasks). A standalone, narrowly-scoped story (1-2 tasks, matching
     `REQ-SB-64-US-01`'s own comparably small "one generalized mechanism"
     shape) is a cleaner unit of work.
  - **Precedent this mirrors:** `REQ-SB-54-US-01-T01` built `replace_body_
    section` itself as a foundational TASK inside a larger story (because at
    that time it had exactly one concrete consumer, Customer/Project). Here,
    by contrast, the mechanism has TWO concrete, near-simultaneous consumers
    from day one (Thread and Meeting) plus an explicit vault-wide framing —
    closer in shape to `REQ-SB-64-US-01`'s own standalone "generalize a
    shared gateway mechanism" story than to a task nested inside one
    consumer's own story.

## Acceptance Criteria

<!-- Written as untagged Gherkin (Given/When/Then). Happy path first, then edge
cases and error states. Do NOT add AC-IDs — the decomposer assigns them at
/plan-tasks. -->

### Scenario 1: A caller writes to a section on its own declared allow-list — unregressed

```gherkin
Given an already-shipped caller of replace_body_section (e.g. thread_
    match_merge regenerating a real Thread's ## Summary) is assigned its
    own real, declared allow-list that includes ## Summary
When that caller calls replace_body_section for ## Summary, exactly as it
    already does today
Then the write succeeds and the section's content is regenerated exactly
    as it was before this story shipped — no regression to any of the 4
    already-shipped call sites
```
<!-- AC-ID: REQ-SB-71-US-01-AC-01 -->

### Scenario 2: A caller attempting to write outside its own allow-list is rejected outright

```gherkin
Given a caller's own declared allow-list does not include a given header
    (e.g. a caller whose allow-list is ["## Summary"] only)
When that caller calls replace_body_section naming a header outside its
    own allow-list (e.g. "## Personal Notes")
Then the call is rejected outright — no write is performed, and the
    section's existing content (if any) is left byte-for-byte unchanged
  And the rejection is a real, observable, honest failure (raised or
    returned as an explicit error), never a silent no-op indistinguishable
    from "header not found"
```
<!-- AC-ID: REQ-SB-71-US-01-AC-02 -->

### Scenario 3: A human-owned section is still readable for context, never writable by any agent code path

```gherkin
Given a note carries a real human-owned section (e.g. a Thread's own
    ## Personal Notes, containing operator-written content)
When any agent code path reads that section's content (e.g. via read_body_
    section, for context ahead of regenerating an adjacent agent-owned
    section)
Then the read succeeds and returns the section's real content unchanged
  And no agent code path is ever able to successfully call replace_body_
    section against that same header — the guard applies uniformly to
    every declared human-owned section, not only the ones this story
    happens to test explicitly
```
<!-- AC-ID: REQ-SB-71-US-01-AC-03 -->

### Scenario 4: Every existing real caller keeps working once each is assigned its own correct allow-list

```gherkin
Given the 4 real, already-shipped replace_body_section call sites (Thread
    ## Summary and ## Related in email_classification.py; Thread ##
    Summary in thread_summary_backfill.py; Customer/Project ## Glimpse and
    ## Background in project_customer_synthesizer.py) each gain their own
    correct, declared allow-list as part of this story
When each of those already-shipped code paths runs again, unmodified in
    its own internal logic
Then every one of them still produces the identical output it did before
    this story shipped — this story only adds a guard around calls that
    were already correct, it does not change what any of them writes
```
<!-- AC-ID: REQ-SB-71-US-01-AC-04 -->

## Affected Screens

None — backend only. No `html-prototype/` screen renders any indication of
which sections are agent- vs. human-owned; this is an internal,
code-enforced write guard with no new UI surface.

## Dependencies

- **Blocked by:** none — `replace_body_section` (`ADR-042` point 2) and its
  4 real call sites are already `Done`.
- **Related to, consumed by:** `REQ-SB-71-US-02` (Email Capture Redesign) —
  its own new Thread `## Summary` regeneration must be assigned a correct
  allow-list from day one, never landing ungated even briefly; hard
  `depends_on`.
- **Related to, consumed by:** `REQ-SB-71-US-03` (Meeting Capture Redesign) —
  its own new Meeting `## Summary`/`## History` regeneration must be
  assigned a correct allow-list from day one; hard `depends_on`.
- **Related to:** `REQ-SB-54-US-01` (`Done`, `ADR-042`) — built `replace_
  body_section` itself; this story extends it, never rewrites its own
  header/next-header location logic.
- **Related to:** `REQ-SB-67-US-01` (`Done`) — real per-Thread `## Summary`
  synthesis + backfill, one of the 4 existing call sites this story
  retrofits with a correct allow-list.
- **Related to:** `REQ-SB-57-US-01` (`Done`) — Customer/Project `##
  Glimpse`/`## Background` synthesis, the other 2 existing call sites.
- **Related to:** `REQ-SB-69-US-01` (`Done`) — Thread's `## Related`
  wikilink regeneration, the 4th existing call site.
- **External:** none.

## Constraints

- **Exactly two rules, per the operator's own explicit choice** — ownership-
  typing every section (agent-owned or human-owned, never hybrid) plus a
  code-level guard on `replace_body_section`. **No snapshot-before-write
  safety net, and no extra approval gate beyond what `REQ-SB-57`'s existing
  `Background`-amendment Pending-Approval flow already provides** — the
  operator explicitly declined the heavier four-rule version discussed.
- **A rejected write must fail loudly and honestly** — never a silent
  no-op that reads the same as "header not found," and never a partial
  write.
- **Every one of the 4 already-shipped call sites must be assigned its own
  correct allow-list as part of this story** — this is a retrofit of the
  CALL SITE's own declared identity/allow-list only, never a change to what
  any of them already writes (Scenario 4).
- **Scope is exactly `vault_writer.replace_body_section`** — this story does
  NOT extend the same enforced-allow-list mechanism to
  `append_body_section_line`, `insert_body_line_if_missing`,
  `replace_body_opening_line`, or any other body-writing primitive; the
  PRD's own text names `replace_body_section` specifically (see
  `## Non-Goals`).
- Must respect the `api → business → data_access` layer boundary
  (`ADR-003`).

## Implementation Tasks

<!-- Analyst-authored starting point, non-authoritative — the decomposer's
own table at /plan-tasks supersedes this. -->

<!-- Decomposer table, /plan-tasks, 2026-08-18 — supersedes the analyst's
starting-point table above. -->

| ID | Type | Task | Files / Area | Depends On | Task File |
|---|---|---|---|---|---|
| REQ-SB-71-US-01-T01 | backend | New `app/data_access/section_ownership.py` (`_HUMAN_OWNED_HEADERS`, `_CALLER_ALLOW_LISTS` seeded with the 4 real callers' correct entries, `is_header_allowed`, `SectionWriteNotAllowed`); `replace_body_section` gains the REQUIRED keyword-only `caller: str` parameter and calls the guard | `app/data_access/vault_writer.py`, `app/data_access/section_ownership.py` (new) | — | `../Tasks/REQ-SB-71-US-01-T01-section-ownership-allow-list-guard.md` |
| REQ-SB-71-US-01-T02 | backend | Retrofit all 6 physical, already-shipped `replace_body_section` call sites across the 4 real callers (`email_classification.thread_match_merge` x2, `thread_summary_backfill.backfill_thread_summaries` x1, `project_customer_synthesizer.py`'s 3 functions x1 each) with their own correct `caller=` id — no change to any of their own internal write logic | `app/business/email_classification.py`, `app/business/thread_summary_backfill.py`, `app/business/project_customer_synthesizer.py` | T01 | `../Tasks/REQ-SB-71-US-01-T02-retrofit-existing-callers.md` |

## Definition of Done

- [x] All acceptance-criteria scenarios pass
- [x] Every Implementation Task above is complete (or explicitly dropped with reason)
- [x] All Constraints respected
- [x] Automated tests added/updated and passing (once test tooling exists) — n/a, test tooling still pending; manual verification mode used throughout, per `Implementation/Pipeline.md`
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Extending the same enforced allow-list to `append_body_section_line`/
  `insert_body_line_if_missing`/`replace_body_opening_line`/any other
  writer primitive** — the PRD's own text names `replace_body_section`
  specifically; this is a real, disclosed narrower scope, not an
  oversight. A Thread's `## Attachments`/`## Transcript` (grown via
  `append_body_section_line`) and a note's own raw-write path (`write_note`)
  are not guarded by this story.
- **A snapshot-before-write safety net, or any new approval gate beyond
  `REQ-57`'s existing `Background`-amendment flow** — explicitly declined
  by the operator.
- **Any change to WHAT any of the 4 existing callers regenerates** — only
  their own declared allow-list identity is added; their own synthesis
  logic is untouched.
- **Assigning allow-lists to `REQ-SB-71-US-02`/`-US-03`'s own NEW call
  sites** — those stories each register their own new caller/allow-list
  against the mechanism this story builds, as part of their own scope, not
  this one's.

## Notes

**Prototype parity:** N/A — no `html-prototype/` screen change; this is a
backend, code-level safety guard.

**Mechanism-level question left to `/plan-tasks`, not resolved by this
pass (per this project's own established analyst/architect role
boundary):** the exact shape of "a caller" — a `caller` string ID parameter
on `replace_body_section` checked against a small, composed-alongside
registry module (e.g. `section_ownership.py`, mirroring `section_registry.
py`'s own "compose alongside, don't reopen" precedent, `ADR-014`), a
decorator, or something else. This story's own Scenarios specify the
OUTCOME (an out-of-allow-list write is rejected; an in-allow-list write is
unaffected) without dictating that shape, mirroring `REQ-SB-69-US-01`'s and
`REQ-SB-64-US-01`'s own identical "specify the outcome, leave the mechanism
to the architect" precedent.

**Why `gate: clear`:** the PRD's own text is unusually explicit for this
specific point — the two-rule scope was directly confirmed by the operator
("1 and 2 is enough"), the one real test it names is concrete and
unambiguous, and this pass's own scoping decision (standalone story, not
folded into Email or Meeting) is grounded in a directly-cited textual
reading of the PRD ("not specific to Threads/Meetings... cross-cutting,
foundational") plus real code facts (4 existing call sites, independently
testable), not a coin-flip among equally-valid readings. No material
assumption was made to fill a gap (trigger 1); `REQ-SB-71` carries no
`<!-- Draft -->` marker — finalized text (trigger 2 n/a); no ADR created/
changed by this analyst pass (trigger 3 n/a for this role); no
`ESCALATIONS.md` entry written (trigger 4 n/a); not oversized — 2 tasks,
comparable to `REQ-SB-64-US-01`'s own similarly-shaped standalone mechanism
story (trigger 5 n/a); no contradictory PRD inputs (trigger 7 n/a); the
one real scoping-latitude question (standalone vs. folded) was resolved
with disclosed, code-grounded reasoning above, not guessed among equally
plausible options (trigger 8 n/a).

gate: clear 2026-08-18 — no MUST-FLAG trigger fired (see the itemized
trigger-by-trigger reasoning above). [Analyst pass — see the architect
addendum immediately below for the trigger-3 flag added at `/plan-tasks`,
and for the mechanism-level question this story's own `## Notes` left
open, now resolved.]

---

**Architect addendum (2026-08-18, `/plan-tasks` step 1):**

**Mechanism resolved:** a `caller: str` REQUIRED keyword-only parameter on
`vault_writer.replace_body_section` (a deliberate breaking-signature
change — every call site, present and future, must explicitly declare
identity), checked against a new, composed-alongside `app/data_access/
section_ownership.py` (data_access layer, mirrors `ADR-014`'s own "compose
alongside, don't reopen" precedent — `ADR-003`'s layering means this
registry cannot live in `app/business`, since `replace_body_section`
itself performs the check). Two structural rules: (1) `_HUMAN_OWNED_
HEADERS = frozenset({"## Personal Notes", "## Actions"})`, checked FIRST
and unconditionally — never overridable by any caller's own allow-list,
by construction (this is what makes Scenario 3's "applies uniformly...
not only the ones this story happens to test explicitly" a structural
guarantee, not caller discipline); (2) `_CALLER_ALLOW_LISTS: dict[str,
frozenset[str]]`, deny-by-default, keyed by the calling FUNCTION
(`module.function`, not the calling module — least-privilege:
`project_customer_synthesizer.py`'s own three real call sites get three
DISTINCT caller ids, since `synthesize_project` has no legitimate reason
to ever write `## Background`). A `SectionWriteNotAllowed(PermissionError)`
is raised on a disallowed write — a real, observable failure, distinct
from `replace_body_section`'s own separate, unchanged "header not found"
`False`-return contract. Full registry (all 4 real call sites, retrofitted
per `T02`, plus every other caller this batch's own `US-02`/`US-03`
register): `Implementation/Architecture/architecture.md` → "Vault Base
Provisioning + Redesigned Email/Meeting Capture..." §"Section-Ownership
Enforcement (`REQ-SB-71-US-01`)".

**Architecture scope:** the coder is bounded to that same subsection
(`app/data_access/vault_writer.py`'s `replace_body_section` signature
change; the new `app/data_access/section_ownership.py` module; the 4
real call sites' own retrofit in `app/business/email_classification.py`,
`app/business/thread_summary_backfill.py`, `app/business/project_
customer_synthesizer.py`). No other subsection of that architecture.md
section applies to this story — `US-02`/`US-03`'s own NEW caller
registrations are explicitly their own scope, not this story's (unchanged
from the analyst's own Non-Goals).

**ADR:** [ADR-048](../Architecture/ADR.md), Decision 2 and Alternatives
Considered 1-3 (per-caller-ad-hoc and per-module granularity both
considered and rejected in favor of the per-function registry above).

**Why `gate: flagged` now, despite the analyst's own `gate: clear` above:**
trigger-3 fired — this architect pass created `ADR-048`, and this story
(the root of this batch) is one of the four it covers; the mechanism-level
question this story's own `## Notes` explicitly deferred to `/plan-tasks`
is resolved above, not guessed. Per `Implementation/Pipeline.md`, this
does NOT halt the pipeline — the decomposer still runs next on all four
stories. A `REVIEW-QUEUE.md` entry has been added.

---

**Decomposer addendum (2026-08-18, `/plan-tasks` step 2):**

All 4 Scenarios locked as `REQ-SB-71-US-01-AC-01`..`AC-04`, wording
unchanged from the analyst's own text. Two tasks, matching the architect's
own two-part mechanism exactly:

- `T01` ships the guard itself (`section_ownership.py` + the
  `replace_body_section` signature change) — this is where `AC-02`
  (rejection) and `AC-03` (human-owned sections always unwritable,
  uniformly) are verified, since both are pure properties of the guard
  mechanism, directly testable the moment the registry exists, without
  needing the real call sites retrofitted first.
- `T02` retrofits the 4 real callers (6 physical call sites) with their own
  `caller=` id — this is where `AC-01` (an allow-listed caller stays
  unregressed) and `AC-04` (all 4 keep working identically) are verified,
  since both require the real call sites to actually declare identity.

**This is the deliberate, explicit, un-missable retrofit task the human
requesting this batch specifically called out** — `T02` enumerates all 6
physical invocations by name (confirmed via direct repo-wide search:
`email_classification.py` lines 367/400 inside `thread_match_merge`;
`thread_summary_backfill.py` line 48; `project_customer_synthesizer.py`
lines 109/206/251 across its 3 functions) so none can be silently missed —
`T02` cannot be marked `Done` while any of the 6 still calls the old,
now-invalid 3-positional-argument signature (a loud `TypeError` at import/
call time makes a missed site impossible to ship unnoticed, by
construction).

`T02` `depends_on: [T01]` — a straight two-task chain, no fan-out, no
fan-in. `T01` has no dependency of its own (`replace_body_section`
(`ADR-042` point 2) and its 4 real call sites are already `Done`, per this
story's own `## Dependencies`).

**Status → `Ready`; `gate` left `flagged`** (architect's own `ADR-048`
flag, not cleared by this pass). No new MUST-FLAG trigger fired during
this decomposer pass: no material assumption (trigger 1 n/a — the
retrofit's own call-site enumeration is a direct repo-wide-search fact,
not a guess); nothing `<!-- Draft -->` (trigger 2 n/a); this pass did not
itself touch `ADR-048` (trigger 3 n/a for this role); no `ESCALATIONS.md`
entry (trigger 4 n/a); not oversized — 2 tasks, matching the analyst's own
sizing comparison to `REQ-SB-64-US-01` (trigger 5 n/a); every locked AC
got a tagged verification step (trigger 6 n/a); no contradictory inputs
(trigger 7 n/a); the two-task split is the only reasonable shape given the
mechanism/retrofit distinction — not a coin-flip among equally-valid
breakdowns (trigger 8 n/a).

**AC → verification mapping:** `AC-01`, `AC-04` tagged in `T02`; `AC-02`,
`AC-03` tagged in `T01`. No locked AC is left unverified.

**Cross-story consumption, for the record (not this story's own scope to
build):** `REQ-SB-71-US-02` registers `email_classification.
synthesize_thread` and its own Files-companion caller against this same
`section_ownership._CALLER_ALLOW_LISTS` registry, as part of its own
tasks (`REQ-SB-71-US-02-T05`, `-T07`); `REQ-SB-71-US-03` registers
`meeting_classification.classify_recent_meetings` the same way
(`REQ-SB-71-US-03-T01`). Each of those tasks `depends_on`
`REQ-SB-71-US-01-T01` (the guard + registry must exist first) — never on
`T02` (the old-caller retrofit is unrelated to a brand-new caller's own
registration).

gate: flagged (unchanged, architect's own `ADR-048` trigger-3) — decomposer
pass added nothing new to flag. See `REVIEW-QUEUE.md`'s existing
`REQ-SB-70-US-01 + REQ-SB-71-US-01 + REQ-SB-71-US-02 + REQ-SB-71-US-03`
entry (already covers all four stories in this batch; not duplicated
here).

---

**Coder addendum (2026-08-18, `/implement-sprint SPRINT-060`):**

`T01` and `T02` both built and verified `Done`, in dependency order.
`T01`'s `AC-02`/`AC-03` verified via a throwaway script (explicitly
authorized by `T01`'s own `## Tests`) against a real Thread note in the
real operator vault. `T02`'s `AC-01`/`AC-04` verified via real, live API
calls: real on-demand email capture (`POST /agents/email-capture-pipeline/
schedules/{pull_email,process_staged_email}/run-now`) exercised
`thread_match_merge` for real (4 real Thread notes, both `## Summary` and
`## Related` written); real `POST /poc/backfill-thread-summaries`
exercised `backfill_thread_summaries` for real (4/4 regenerated); approving
a real, freshly-created `route_thread_to_project` Pending Approval via
`POST /pending-approvals/{id}/approve` exercised both `synthesize_project`
and `synthesize_customer` for real (both wrote real `## Glimpse` content).
`finalize_background_amendment_proposal`'s own full live end-to-end
trigger requires a real `propose_background_amendment` Pending Approval,
none of which exist in this vault right now (its only real trigger,
`synthesize_customer`'s `evidence_text` path, has no currently-reachable
real caller since the legacy-flat-Customer-note migration already ran) —
disclosed, not hidden, in `T02`'s own Implementation Log, with
compensating evidence (unchanged-code-diff + the exact caller/header pair
proven allowed and functional at the guard layer via `T01`'s own script).
No regression found in any of the 4 real callers / 6 physical call sites.
Story status → `Done`. `gate` left `flagged` — the architect's own
`ADR-048` human-review flag is not this role's to clear; see
`REVIEW-QUEUE.md`.
