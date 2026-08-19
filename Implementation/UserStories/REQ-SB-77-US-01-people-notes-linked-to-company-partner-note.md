---
id: REQ-SB-77-US-01
title: People Notes Retroactively Linked to Their Real Company/Partner Note
requirement_ids: [REQ-SB-77]
requirement_section: "REQ-SB-77: People Notes Linked to Their Real Company/Partner Note"
phase: P2
status: Ready
gate: clear
gate_reason: "was flagged trigger-4 (ESC-057, requirement premise partially contradicted by already-shipped REQ-SB-10/ADR-009 code) + trigger-8 (multiple equally-valid trigger-mechanism shapes). Trigger-8 resolved directly by the operator when offered the real options: 'Both: instant on approval + self-healing in REQ-79's pipeline' — the retroactive Person-relink hooks into REQ-SB-76's batch-apply finalize (immediate, on a company's status actually changing) AND is folded into REQ-SB-79's 'Company and Partner Building' sub-pipeline as a periodic self-healing catch-all. ESC-057 stays Open (a real, permanent log entry, not reopened) — its own resolution is this story's real build, not this gate clear. See ## Notes."
sprint: "SPRINT-074"
created: 2026-08-19
updated: 2026-08-19
---

# REQ-SB-77-US-01 — People Notes Retroactively Linked to Their Real Company/Partner Note

## Story

**As a** Second Brain operator
**I want** every already-existing Person note whose derived company later
becomes a real, known Customer, Partner, or Affiliate to actually gain its
real wikilink to that company's concept file — reachable as a real,
on-demand capability, not something I have to remember to trigger through a
`/poc/` route — while a Person with no determinable or not-yet-tracked
company stays a normal, unblocked entry
**So that** my People vault stays graph-connected as company-tracking data
matures over time (especially as `REQ-SB-76`'s Company Review approvals
confirm new Customers/Partners/Affiliates), without a manual, easy-to-forget
retrofit step

## Context

- PRD: `Documentation/PRD.md` → *REQ-SB-77: People Notes Linked to Their
  Real Company/Partner Note*. Raised 2026-08-19, operator: "People should be
  linked to a Company or in the People Seaction if no COmpany is found for
  them" — deliberately deferred out of `REQ-SB-76`'s own scope at the
  operator's explicit direction ("log the Rest as REQ and we pick them
  next"). No `<!-- Draft -->` marker on this requirement.
- **The requirement's own stated premise does not match the real, current
  code, confirmed live this pass — see `ESC-057` for the full disclosure.**
  In short: `app/business/people_extraction.py::ensure_person_note`
  (already `Done`, `REQ-SB-10`/`REQ-SB-71-US-03-T03`/`ADR-009`) already
  derives a Person's company from their email domain, tags it
  `company/<slug>` (`build_person_tags`), and — **only when that company
  already matches a known Customer or Partner** (`find_matching_customer`/
  `find_matching_partner`, against `vault_writer.list_known_customers()`/
  `list_known_partners()`) — ensures the matching hub note exists and links
  this Person note to it (`customer_hub_linking.link_note_to_customer_hub`
  / `partner_hub_linking.link_note_to_partner_hub`, a real inline
  `**Customer:**`/`**Partner:** [[Hub]]` wikilink), plus nests a
  newly-created note under `Work/Customers/<slug>/People/` for a
  Customer match (Partner has no OKF directory shape to nest under —
  `partner_hub_note_path` is a flat file, confirmed by direct reading of
  `partner_hub_linking.py`/`vault_writer.py`, so this is a structural
  non-gap, not a bug). This matching is **re-checked on every call, not
  just at note creation** — the function's own docstring names this
  explicitly: "a company that later becomes a known customer or partner
  gets its wikilink added retroactively on the next call, without touching
  anything else." A retrofit entry point that re-runs this for every real
  Email sender already exists (`retrofit_people_from_emails`) and is
  already reachable via `POST /poc/retrofit-people-from-emails`
  (`app/api/email_poc_router.py:66-68`, confirmed live).
  The requirement's premise IS accurate for the common, disclosed residual
  case — a company that is NOT (yet) a known Customer/Partner gets its
  `company/<slug>` tag and nothing else (no hub note exists to link to) —
  and for the "no company at all" case (personal/free email domain, or no
  email) — neither tag nor link. The operator's own live observation of an
  un-linked Person note is real and consistent with this residual case; the
  PRD's own blanket "no real wikilink" framing is the part that overstates
  it.
- **The one genuinely new, buildable gap given the above:** the retroactive
  re-linking mechanism already exists in code but is reachable only through
  a `/poc/` route, with no automatic trigger point tied to the moment a
  company's Customer/Partner/Affiliate status actually changes (e.g.
  `REQ-SB-76`'s own batch-apply). This story's own new scope is closing
  THAT gap — making the already-correct linking outcome reliably reachable
  — not rebuilding the linking mechanism itself.
- **Affiliate coverage confirmed by direct reading, not assumed:**
  `list_known_customers()`/`list_known_partners()` derive their lists from
  real `customer:`/`partner:` frontmatter usage across the vault (not a
  separate registry) — an Affiliate entity created by `REQ-SB-76`'s own
  Affiliate outcome (a normal Customer- or Partner-kind entry with
  `affiliate_of` set) is picked up by this exact same scan automatically,
  with zero special-casing needed in `people_extraction.py`.
- **`REQ-SB-76-US-01`** (Company Review, `Draft`, `gate: flagged`, sprint
  `SPRINT-072` `In Progress` as of this pass) is the main real-world path
  that will grow the known-Customer/Partner list going forward and is the
  operator's own original context for raising this requirement — but this
  story's own Gherkin holds regardless of whether `REQ-SB-76-US-01` has
  shipped, since the retroactive-linking mechanism it exercises already
  works for ANY company that becomes known via ANY path (not only
  `REQ-SB-76`'s own approval flow). No hard dependency (see `## Dependencies`).

## Acceptance Criteria

### Scenario 1: A Person note whose company becomes a known Customer after the note already existed gains its real wikilink, without being moved

```gherkin
Given a real Person note already carrying a company/<slug> tag only, for a
    company that was NOT yet a known Customer or Partner when the note was
    created
When that company is later confirmed as a real Customer (via REQ-SB-76's
    approval flow or any other path list_known_customers() draws from) and
    the re-linking capability is invoked for that Person — either
    people_extraction.relink_people_for_thread_paths() (the new bounded,
    per-Thread trigger) or the already-existing, whole-vault
    retrofit_people_from_emails()
Then the Person note's own body gains the real **Customer:** [[Hub]]
    wikilink to that Customer's concept file, while the note's own existing
    location on disk is left completely unchanged — never moved or
    duplicated
```
<!-- AC-ID: REQ-SB-77-US-01-AC-01 -->

### Scenario 2: The same retroactive linking works for a company confirmed as a Partner

```gherkin
Given a real Person note already carrying a company/<slug> tag only, for a
    company that was NOT yet a known Customer or Partner when the note was
    created
When that company is later confirmed as a real Partner and the re-linking
    capability is invoked for that Person (either trigger named in
    Scenario 1)
Then the Person note's own body gains the real **Partner:** [[Hub]]
    wikilink to that Partner's hub note, with its own existing location left
    unchanged
```
<!-- AC-ID: REQ-SB-77-US-01-AC-02 -->

### Scenario 3: A company confirmed as an Affiliate of an existing Customer or Partner links Person notes to the Affiliate's own concept file, with no special-casing

```gherkin
Given a real Person note tagged for a company that is later approved via
    REQ-SB-76's Affiliate outcome (a real Customer- or Partner-kind entity
    with its own affiliate_of value set)
When the re-linking capability is invoked for that Person (either trigger
    named in Scenario 1)
Then the Person note gains the real wikilink to the Affiliate's own concept
    file, exactly as Scenario 1/2 — the Affiliate entity is picked up by the
    same known-Customer/Partner scan as any other entry, with no separate
    Affiliate-specific linking mechanism needed
```
<!-- AC-ID: REQ-SB-77-US-01-AC-03 -->

### Scenario 4: A Person whose company is still not a known Customer or Partner remains a normal, unblocked entry

```gherkin
Given a real Person note tagged company/<slug> for a company that matches
    neither a known Customer nor a known Partner
When the re-linking capability runs (whether invoked for this one Person's
    own Thread or as part of a full-vault pass)
Then the Person note is left with its company/<slug> tag and no wikilink,
    at its normal location, completely unblocked — never held back waiting
    for a company match that may never arrive
```
<!-- AC-ID: REQ-SB-77-US-01-AC-04 -->

### Scenario 5: A Person note with no determinable company at all is left completely unchanged

```gherkin
Given a real Person note derived from a personal/free-email-provider domain
    or with no email at all, carrying no company tag
When the re-linking capability runs
Then the Person note is left completely unchanged — no tag, no wikilink,
    no location change
```
<!-- AC-ID: REQ-SB-77-US-01-AC-05 -->

### Scenario 6: The re-linking capability fires two ways — instantly on a company's status changing, and self-healing on a schedule

```gherkin
Given the retroactive-linking mechanism this story exercises (Scenarios
    1-3) already exists in code, reachable today only via the POC-prefixed
    POST /poc/retrofit-people-from-emails endpoint
When this story ships
Then TWO real, durable trigger points exist: (a) librarian_housekeeping.
    finalize_company_review's own thin public wrapper calls the new
    people_extraction.relink_people_for_thread_paths(thread_paths)
    immediately after every real Customer/Partner/Affiliate/Merge outcome
    write succeeds (instant, on a company's status actually changing), and
    (b) REQ-SB-79-US-01's own run_company_partner_building_pass() calls the
    already-existing people_extraction.retrofit_people_from_emails() on its
    own independent schedule (self-healing catch-all) — never only one of
    the two, and never a UI button as the sole mechanism
```
<!-- AC-ID: REQ-SB-77-US-01-AC-06 -->

### Scenario 7: Re-running the re-linking capability against an already-fully-linked vault is a true no-op

```gherkin
Given every real Person note whose company is a known Customer/Partner/
    Affiliate already carries its own correct wikilink
When the re-linking capability is triggered again
Then no Person note's own content or location changes — proving the
    capability is idempotent and safe to trigger repeatedly, mirroring
    ensure_person_note's own already-proven idempotent contract
```
<!-- AC-ID: REQ-SB-77-US-01-AC-07 -->

## Affected Screens

None — both resolved trigger mechanisms (Scenario 6) are backend-only
(a finalize-path call from `REQ-SB-76`, a Job call from `REQ-SB-79`'s
scheduled pipeline). No UI-visible trigger, no new screen.

**Prototype parity:** N/A — no new `html-prototype/` screen region is
mandated by this story's own ACs.

## Dependencies

- **Related to (not a hard blocker):** `REQ-SB-10-US-01` (People Living
  Documents, `Done`) — the original matched-company linking mechanism this
  story re-exposes/closes the reach-gap on, not rebuilds.
- **Related to (not a hard blocker):** `REQ-SB-16-US-01` (Partner Hub Notes,
  `Done`) — the Partner-side half of the same mechanism (`ADR-009`).
- **Hard dependency (Scenario 6a):** `REQ-SB-76-US-01` (Company Review,
  `Draft`, `gate: flagged`, `SPRINT-072` `In Progress`) — its batch-apply
  finalize path is one of the two real trigger points this story wires
  into; the hook itself can be built once `REQ-SB-76`'s finalize function
  signature exists, but genuinely needs that function to call into.
- **Hard dependency (Scenario 6b):** `REQ-SB-79-US-01` (Librarian Two
  Sub-Pipelines, `Draft`) — the "Company and Partner Building" pipeline
  this story's own self-healing catch-all runs inside of.
- **External:** none new.

## Constraints

- **Never move or duplicate an already-existing Person note.** Mirrors
  `ensure_person_note`'s own already-shipped, explicit contract — an
  existing note is topped up in place, never relocated, even when its
  newly-derived Customer/Partner differs from where it already lives.
- **Never re-derive or override an existing note's own manually-edited
  fields** (phone/linkedin/etc.) — this story only concerns the
  tag/wikilink/company-match surface `ensure_person_note` already owns.
- **No new linking primitive.** Every wikilink this story's own re-linking
  capability writes goes through the already-shipped
  `customer_hub_linking.link_note_to_customer_hub` /
  `partner_hub_linking.link_note_to_partner_hub`, never a new, third
  mechanism.
- **Idempotent and safe to trigger repeatedly** (Scenario 7) — never a
  one-off script (`MEMORY.md` — API-first, no script workarounds).
- Must respect the `api → business → data_access` layer boundary (`ADR-003`).

## Implementation Tasks

<!-- Decomposer-authored table (/plan-tasks step 2, 2026-08-19) — supersedes
the analyst's provisional table. Splits Scenario 6 into an instant-hook task
(no cross-story dependency) and a scheduled-self-heal verification task that
carries a REAL, recorded depends_on edge onto REQ-SB-79-US-01-T02 (the task
that creates run_company_partner_building_pass()) — see "Cross-story
dependency" note below. -->

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| REQ-SB-77-US-01-T01 | backend | New `people_extraction.relink_people_for_thread_paths(thread_paths)` — bounded, per-Thread sibling of `retrofit_people_from_emails`, reusing `ensure_person_note` verbatim | `app/business/people_extraction.py` | `../Tasks/REQ-SB-77-US-01-T01-relink-people-for-thread-paths.md` |
| REQ-SB-77-US-01-T02 | backend | Instant trigger (Scenario 6a): retarget `librarian_housekeeping.finalize_company_review` to a thin public wrapper around a renamed `_finalize_company_review_outcome`, calling `relink_people_for_thread_paths` after every outcome write succeeds | `app/business/pipelines/librarian_housekeeping.py` | `../Tasks/REQ-SB-77-US-01-T02-instant-relink-hook.md` |
| REQ-SB-77-US-01-T03 | backend | Scheduled self-heal (Scenario 6b): verification-only — confirms `run_company_partner_building_pass()` (built by `REQ-SB-79-US-01-T02`) genuinely drives `retrofit_people_from_emails()` on its own schedule. **Real cross-story `depends_on`.** | `app/business/pipelines/librarian_housekeeping.py` (verification only; in-scope fix only on a genuine live-found defect) | `../Tasks/REQ-SB-77-US-01-T03-scheduled-self-heal-verification.md` |
| REQ-SB-77-US-01-T04 | backend | Live verification pass across the real vault: Scenarios 1-5/7 against real Person notes with real company matches/non-matches, including a real before/after check that no existing note is moved or duplicated | `app/business/people_extraction.py` | `../Tasks/REQ-SB-77-US-01-T04-live-verification.md` |

## Definition of Done

- [ ] All acceptance-criteria scenarios pass
- [ ] Every Implementation Task above is complete (or explicitly dropped with reason)
- [ ] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists)
- [ ] `MEMORY.md` updated with any new decisions / patterns / constraints
- [ ] `CHANGELOG.md` entry appended

## Non-Goals / Out of Scope

- **Rebuilding or changing the matched-company linking mechanism itself**
  (`ensure_person_note`, `find_matching_customer`/`find_matching_partner`,
  `build_person_tags`) — already correct and already shipped; this story
  only closes the reach gap around triggering it.
- **Re-nesting an already-existing Person note under a newly-matched
  Customer's `People/` folder** — `ensure_person_note`'s own established
  "topped up in place, never moved" contract is preserved, not revisited
  (Scenario 1's own explicit "location unchanged" clause).
- **Giving Partner an OKF directory shape / a `People/` nesting concept of
  its own** — `partner_hub_note_path` staying a flat file is a structural,
  pre-existing, disclosed design (`ADR-009`), not something this story
  changes.
- **Automatically wiring this capability into `REQ-SB-76-US-01`'s own
  batch-apply as the ONLY trigger mechanism** — one of several equally-valid
  mechanism choices for Scenario 6, left to the architect, not asserted
  here as the mandated shape.

## Notes

**Gate cleared 2026-08-19 — trigger 8 resolved directly by the operator:**
offered the real, named options (manual / on-approval only / scheduled
only / both), the operator picked "Both: instant on approval + self-
healing in REQ-79's pipeline" — the recommended option, and now the
locked design for Scenario 6 above. `ESC-057` stays `Open` in
`ESCALATIONS.md` (a permanent log entry, not reopened) — its own real
resolution is this story shipping, not this gate clear.

**Why this pass fires trigger 4 (ESCALATIONS.md entry) and trigger 8
(unclear/multiple equally-valid interpretations):** `ESC-057` (below)
records the real discrepancy found this pass between `REQ-SB-77`'s own PRD
premise ("no real wikilink... confirmed live") and the actual, already-
shipped `people_extraction.py`/`customer_hub_linking.py`/
`partner_hub_linking.py` mechanism, which already produces a real wikilink
for the matched-company case and already self-heals retroactively on
re-run. Given that finding, the one piece of genuinely new, buildable scope
— making the existing retroactive-linking outcome reliably reachable
(Scenario 6) — has multiple equally-valid mechanism shapes (a manual
trigger, an automatic hook off `REQ-SB-76`'s batch-apply, a new scheduled
Librarian pass) with no operator direction narrowing the choice; this pass
writes the Gherkin at the OUTCOME level (mirrors `REQ-SB-73-US-01`'s own
"Gherkin specifies outcome, not mechanism" precedent) and leaves the
mechanism choice to the architect, but still flags for a human decision on
whether this scoping (rather than, say, treating `REQ-SB-77` as already
substantially satisfied and closing it as a documentation-only correction)
is the right call.

**Why this does NOT trip trigger 2:** `REQ-SB-77` carries no `<!--
Draft -->` marker — the requirement text itself is finalized; the
discrepancy found is against the CODEBASE, not an internal PRD
inconsistency.

**Why this does NOT trip trigger 3:** no ADR created or changed by this
pass — that's the architect's own trigger, not this role's.

**Why this does NOT trip trigger 5 (oversized):** 2 starting tasks,
smaller than any comparable Librarian-family story to date — the
mechanism this story exercises already exists; the new work is a reach/
trigger promotion plus verification, not a new mechanism build.

**Why this does NOT trip trigger 7 separately from trigger 4:** the
contradiction found IS trigger 4's own subject (an ESCALATIONS entry was
the correct surface for it, per Pipeline.md's "wrote an ESCALATIONS.md
entry" trigger) — not double-counted as a second, distinct trigger-7 event.

**Prototype parity:** N/A — see `## Affected Screens` above.

`gate: flagged` — see `gate_reason` above and `ESC-057`. This does NOT
block `/plan-tasks` from running (the decomposer may still lock ACs and
draft tasks against Scenario 6's own outcome-level wording) — it means a
human should confirm the scoping choice (promote the existing reach gap vs.
some other interpretation) before/alongside `/plan-tasks`, per
`Implementation/Pipeline.md`'s "Promotion of a flagged item" gate.

**What to do next:** see `REVIEW-QUEUE.md` → `REQ-SB-77-US-01` for the
concrete question posed to the human.

---

## Architect pass, 2026-08-19 (`/plan-tasks` step 1)

Note: the frontmatter `gate:` above is the current, authoritative state
(`clear`, per the operator's own live resolution recorded in
`gate_reason`) — the older `gate: flagged` sentence earlier in this `##
Notes` section predates that resolution and is a stale leftover, not
re-asserted by this pass.

**Mechanism for Scenario 6's two trigger points, resolved by direct
composition against real, current code:**

1. **Instant, on a company's status changing.** `librarian_housekeeping.
   finalize_company_review` (`Done`) is retargeted to a thin public
   wrapper around a renamed-in-place private `_finalize_company_review_
   outcome`, adding exactly one new call: `people_extraction.relink_
   people_for_thread_paths(payload["thread_paths"])`, run after the
   outcome's own writes succeed. New function, `people_extraction.
   relink_people_for_thread_paths(thread_paths: list[str]) -> list[dict]`
   — a bounded, per-Thread sibling of the already-existing whole-vault
   `retrofit_people_from_emails()`, reusing `ensure_person_note` verbatim
   (zero new linking primitive, per this story's own Constraint). This
   half needs NOTHING from `REQ-SB-79-US-01` — `finalize_company_review`
   already exists today.
2. **Scheduled, self-healing catch-all.** `REQ-SB-79-US-01`'s own new
   `run_company_partner_building_pass()` additionally calls the
   ALREADY-EXISTING `people_extraction.retrofit_people_from_emails()` —
   zero new mechanism, pure wiring. **This half has a real, hard
   `depends_on` on whichever `REQ-SB-79-US-01` task creates that function
   — it cannot be built or verified before that function exists.** See
   `REQ-SB-79-US-01`'s own `## Notes` (architect pass) for the matching
   entry.

**Recommendation to the decomposer:** split this story's own Scenario-6
work into at least two backend tasks — one for the instant hook (no
cross-story dependency, buildable immediately), one for the scheduled
self-heal wiring (`depends_on` the `REQ-SB-79-US-01` task that creates
`run_company_partner_building_pass()`). The product-owner should sequence
the two stories' sprints accordingly (same sprint, or `REQ-SB-79` first
with a recorded `depends_on_sprints` edge).

**Architecture scope:** §"People Notes Retroactively Linked to Company/
Partner" (`Implementation/Architecture/architecture.md`) — bounds the
coder to that section. No section of §"The Librarian — Two Sub-Pipelines"
is in scope for THIS story's own tasks beyond the single named dependency
above.

**Why this pass creates no new ADR:** every decision here is composition
of already-`Accepted` patterns — `ensure_person_note` (`ADR-009`) is
reused verbatim, `relink_people_for_thread_paths` is a narrower-bounded
input to the same operation `retrofit_people_from_emails` already
performs (no new linking primitive), and both trigger points are plain
function calls into already-existing (or, for `run_company_partner_
building_pass`, `REQ-SB-79-US-01`-architected) capabilities. No new tool,
framework, or structural module boundary — confirms the operator's own
working assumption for this story. `gate` stays `clear` (unchanged by
this pass — no trigger 3 fired); this pass's own breadcrumb: gate: clear
2026-08-19 — no new ADR, no new assumption beyond the one real, disclosed
cross-story dependency named above.

---

## ESC-057 (recorded in `ESCALATIONS.md`, referenced here for traceability)

`REQ-SB-77`'s own PRD text ("A Person note currently carries only a
`tags: ["company/<slug>"]` tag... with no real wikilink to that Company's
own Customer or Partner concept file") is contradicted by real,
already-shipped code: `people_extraction.py::ensure_person_note` already
writes a real wikilink (via `customer_hub_linking`/`partner_hub_linking`)
whenever the derived company matches a known Customer or Partner, and
already self-heals this retroactively on every call — confirmed by direct
reading, not assumed. See the full entry in `ESCALATIONS.md` (`ESC-057`)
for category, resolution, and status.

---

## Decomposer pass, 2026-08-19 (`/plan-tasks` step 2)

All 7 Gherkin scenarios locked as `REQ-SB-77-US-01-AC-01` … `AC-07`, tightened
to name the concrete, architect-resolved trigger mechanisms (`relink_people_
for_thread_paths`/`retrofit_people_from_emails`, the `finalize_company_
review` wrapper, `run_company_partner_building_pass`) in place of the
analyst's outcome-level "the operator triggers the re-linking capability"
phrasing — no locked AC's own substance changed, only buildability.

Four tasks, `T01`-`T04` (see `## Implementation Tasks`):

- `T01` — `relink_people_for_thread_paths` (new function). `depends_on: []`.
- `T02` — instant hook (`finalize_company_review` retarget). `depends_on:
  [REQ-SB-77-US-01-T01]`.
- `T03` — scheduled self-heal, verification-only. `depends_on: [REQ-SB-77-
  US-01-T01, REQ-SB-79-US-01-T02]`.
- `T04` — live verification, Scenarios 1-5/7. `depends_on: [REQ-SB-77-US-
  01-T01]`.

**Cross-story dependency (the architect's explicit question to this role)
— resolved as a real, task-level `depends_on` edge, NOT deferred to
`depends_on_sprints`:** `T03` carries `depends_on: [..., REQ-SB-79-US-01-
T02]` — a genuine cross-story task edge, naming the specific `REQ-SB-79`
task that creates `run_company_partner_building_pass()` (confirmed against
`REQ-SB-79-US-01`'s own `## Implementation Tasks` table, this same pass).
Reasoning: `Pipeline.md` Hard Rule 7 ("dependency-linked stories go in the
same sprint **or** in ordered sprints with a recorded `depends_on_sprints`
edge") presupposes the decomposer has already named the real task-level
edge — `depends_on_sprints` is the **product-owner's own downstream
consequence** of an edge the decomposer records now, at `/plan-tasks`, not
a substitute mechanism the decomposer can defer to instead. Recording the
edge here is also what makes it possible for `/plan-sprints` to detect and
honour it at all — a task file with no `depends_on` entry naming
`REQ-SB-79-US-01-T02` would give the product-owner nothing to sequence
against. The product-owner (`/plan-sprints`) resolves the edge concretely:
either the same sprint as `REQ-SB-79-US-01` (if scope allows), or `REQ-
SB-79-US-01`'s own sprint first, with `REQ-SB-77-US-01`'s sprint carrying a
recorded `depends_on_sprints` edge onto it — never routed around.

**Status:** every AC is locked (7/7), every locked AC has at least one
AC-tagged verification step across `T01`-`T04` (`AC-01`/`AC-02`/`AC-03`/
`AC-04`/`AC-05`/`AC-07` in `T04`; `AC-06` split across `T02`'s own instant
half and `T03`'s own scheduled half), and `depends_on` is acyclic (`T01` →
`T02`/`T03`/`T04`, plus the one disclosed cross-story edge `T03` →
`REQ-SB-79-US-01-T02`). Story advances **`Draft` → `Ready`**. `gate: clear`
is unchanged by this pass (already resolved by the operator at the
architect step) — breadcrumb: gate: clear 2026-08-19 — no new MUST-FLAG
trigger fired at this step; the one real cross-story dependency is
disclosed above, not hidden.
