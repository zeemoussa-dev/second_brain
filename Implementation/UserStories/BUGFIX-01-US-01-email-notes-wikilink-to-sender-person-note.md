---
id: BUGFIX-01-US-01
title: Email notes wikilink to their sender's Person note (forward fix + backfill retrofit)
requirement_ids: [BUG-001]
requirement_section: "BUGS.md → BUG-001"
status: Done
gate: clear
gate_reason: ""
sprint: "SPRINT-005"
created: 2026-08-11
updated: 2026-08-11
---

# BUGFIX-01-US-01 — Email notes wikilink to their sender's Person note (forward fix + backfill retrofit)

## Story

**As a** Second Brain user browsing my vault in Obsidian
**I want** every Email note to carry an actual `[[PersonName]]` wikilink to
its sender's Person note — both for every Email note captured from now on and
for every Email note already sitting in the vault
**So that** Person notes show up as connected nodes in Obsidian's graph and
backlinks/"Linked mentions" relative to the emails that actually reference
them, instead of rendering as disconnected dots despite a Person note
existing

## Context

- Bug ledger: `BUGS.md` → `BUG-001` — "Email notes don't wikilink to their
  sender's Person note" (Logic, Major, Open at triage time).
  - **Repro:** open any already-captured Email note under `Work/<Kind>/`
    whose `sender`/`sender_email` frontmatter has a matching Person note
    already created at `Work/People/<sender_email>.md` (via `REQ-SB-10`'s
    per-write hook, `people_extraction.ensure_person_note_for_captured_email`)
    — the Person note never appears in the Email note's body as a link, only
    Obsidian's Graph view / the Person note's own backlinks panel shows the
    gap.
  - **Expected (per `MEMORY.md`'s 2026-08-11 standing rule, tightened the
    same day after this bug was found):** every note that *references*
    another vault entity must carry an actual `[[wikilink]]` to that entity's
    own note, checked in **both directions** — the referencing note must
    link out, not just cause the referenced note to be created as a side
    effect. Email→Person is exactly this gap: the rule was checked for
    Person→Company (outbound) when People was designed, but not for
    Email→Person (inbound).
  - **Actual:** `app/business/email_classification.py`'s
    `classify_recent_emails` writes `sender`/`sender_email` as plain
    frontmatter strings and calls
    `people_extraction.ensure_person_note_for_captured_email(...)` purely for
    its Person-note side effect — the Email note's own body is never touched
    with a link back. Every already-captured Email note has this gap.
  - **Timing note:** a live background full-inbox capture run may have been
    in progress at the moment this bug was found, using the pre-fix code.
    The regression scenario below is written to hold regardless of when any
    given Email note was captured (idempotent retrofit over already-captured
    notes, exact-same behaviour going forward for newly-captured ones) — it
    does not depend on which notes existed at any particular moment.
- `MEMORY.md`'s 2026-08-11 constraint (the one directly load-bearing for this
  fix) also explicitly says a gap like this needs **both** a forward code fix
  **and** a one-time backfill retrofit over already-captured notes — "not
  just a forward-only code fix" — mirroring the retrofit pattern
  `REQ-SB-14`/`REQ-SB-10` already established (one shared operation, used
  once as a one-time batch over `vault_writer.list_all_note_paths()` and once
  as a per-write hook).
- **Where the fix hooks in (read live, not guessed):**
  - `app/business/email_classification.py`'s `classify_recent_emails`
    already calls `people_extraction.ensure_person_note_for_captured_email`
    at the exact point the Email note's body is being assembled, and that
    call's return value (`ensure_person_note`'s result dict) already includes
    `note_path` — the Person note's own path/stem is available right there,
    so wiring the missing link into the body is a small, well-bounded change
    at an existing call site, not new plumbing.
  - The two existing one-time retrofit precedents this fix's retrofit half
    should mirror: `app/business/customer_hub_linking.py`'s
    `retrofit_customer_hub_links` and `app/business/people_extraction.py`'s
    own `retrofit_people_from_emails` — both one-time batch functions that
    walk `vault_writer.list_all_note_paths()` and are idempotent by
    construction.
  - The existing non-destructive body-edit primitive this fix's link
    insertion (both the forward hook and the retrofit) should reuse:
    `vault_writer.insert_body_line_if_missing` — inserts one line only if not
    already present, never touching any other body content, already used by
    `customer_hub_linking.link_note_to_customer_hub` for the exact same kind
    of "one wikilink line" insertion.
- No `html-prototype/` screen applies — like the original `REQ-SB-10-US-01`
  and `REQ-SB-14-US-01` this bug's fix affects, this is backend/vault-content
  work with no application UI surface; Obsidian's own note/graph views are
  the surface this fix changes, not a Second Brain screen.

## Acceptance Criteria

<!-- Locked by the decomposer at /plan-tasks (2026-08-11). The analyst's
single untagged scenario (BUG-001's regression criterion) is split into
three locked ACs, one per independently-verifiable facet — the forward/
backfilled link itself, the retrofit's idempotent rerun, and the blank-
sender_email skip — mirroring the granularity REQ-SB-10-US-01/
REQ-SB-14-US-01 already used for multi-clause scenarios. No observable
behaviour was changed from the analyst's draft; wording was tightened only
for buildability. -->

### Scenario 1: Email note wikilinks to its sender's Person note, forward and backfilled

```gherkin
Given an Email note under Work/<Kind>/ has a non-blank sender_email in its
    frontmatter — whether that note was captured before this fix shipped or
    is captured after it — and a Person note for that sender's email address
    already exists (or is created as part of this same processing) at
    Work/People/<Person>.md
When the Email note is written by the email-capture pipeline going forward,
    or an already-captured Email note is processed by the one-time
    wikilink-backfill retrofit
Then the Email note's body contains an actual [[PersonName]] wikilink to the
    sender's Person note, matching that Person note's own filename stem
```
<!-- AC-ID: BUGFIX-01-US-01-AC-01 -->

### Scenario 2: Retrofit rerun does not duplicate the wikilink

```gherkin
Given an Email note's body already carries the [[PersonName]] wikilink to
    its sender's Person note
When the one-time wikilink-backfill retrofit is run again against that same
    Email note
Then no second, duplicate [[PersonName]] wikilink is added to the note's
    body
```
<!-- AC-ID: BUGFIX-01-US-01-AC-02 -->

### Scenario 3: An Email note with a blank sender_email is left unchanged, without erroring

```gherkin
Given an Email note's sender_email frontmatter value is blank or missing
When that note is processed by the one-time wikilink-backfill retrofit, or
    written by the email-capture pipeline's going-forward hook
Then the note's body is left unchanged
  And the retrofit/capture run completes without erroring on that note
```
<!-- AC-ID: BUGFIX-01-US-01-AC-03 -->

## Affected Screens

None — backend/vault-content only. No `html-prototype/` screen exists or is
needed for this fix; Obsidian's own note body/graph/backlinks views are the
surface this change affects, not a Second Brain application screen.

## Dependencies

- **Blocked by:** none — the per-write Person-note creation hook
  (`app/business/people_extraction.py`, `REQ-SB-10-US-01`, Done) and the
  email-capture pipeline (`app/business/email_classification.py`,
  `REQ-SB-07-US-01`, Done) this fix wires into already exist and work.
- **Related to:** `REQ-SB-10-US-01` — this fix closes the exact gap that
  story's own outbound-link check missed on the inbound (Email→Person)
  direction; reuses its `ensure_person_note_for_captured_email` return value.
- **Related to:** `REQ-SB-14-US-01` — this fix's retrofit half mirrors its
  `retrofit_customer_hub_links` one-time-batch shape and its
  `insert_body_line_if_missing` non-destructive body-edit primitive.
- **External:** none new. Runs against the user's real, live Obsidian vault
  at the path configured in `src/backend/.env`'s `VAULT_PATH`, not a
  fixture/test vault — same as the original `REQ-SB-10-US-01`/
  `REQ-SB-14-US-01` retrofits.

## Constraints

- Must respect the `api → business → data_access` layer boundary (ADR-003).
- The link insertion (both the forward hook and the retrofit) must use a
  non-destructive, idempotent insert — never rewrite the Email note's body
  wholesale, never duplicate the link line on a rerun. Mirrors
  `vault_writer.insert_body_line_if_missing`'s existing idempotent-insert
  precedent.
- The retrofit must be idempotent and safe to rerun against the real, live
  vault — rerunning must never create a duplicate wikilink or otherwise
  disturb an Email note's existing body content, same no-data-loss bar the
  `REQ-SB-10-US-01`/`REQ-SB-14-US-01` retrofits were held to.
- An Email note with no `sender_email` (or one whose sender never resolved to
  a Person note) is skipped, not errored — same skip behaviour
  `people_extraction.retrofit_people_from_emails` already applies.
- The exact wikilink line format/placement in the Email note body (e.g.
  matching the `**Customer:** [[Hub]]` / `**Company:** [[ADNOC]]` inline-line
  convention already used elsewhere) is an architecture-level detail for
  `/plan-tasks`, not decided here — this story specs the observable outcome
  (an actual `[[PersonName]]` wikilink present in the body), not the exact
  string.
- This work runs against the user's real, live Obsidian vault, not a
  fixture/test vault — no-data-loss and idempotency are load-bearing, not
  conveniences.

## Implementation Tasks

| ID | Type | Task | Files / Area | Task File |
|---|---|---|---|---|
| BUGFIX-01-US-01-T01 | backend | Add `link_email_to_person` primitive; wire it into the going-forward capture hook | `src/backend/app/business/people_extraction.py`, `src/backend/app/business/email_classification.py` | [T01](../Tasks/BUGFIX-01-US-01-T01-link-email-to-person-forward-hook.md) |
| BUGFIX-01-US-01-T02 | backend | New `retrofit_email_sender_links` batch + `POST /poc/retrofit-email-sender-links` endpoint | `src/backend/app/business/people_extraction.py`, `src/backend/app/api/email_poc_router.py` | [T02](../Tasks/BUGFIX-01-US-01-T02-retrofit-email-sender-links-endpoint.md) |

## Definition of Done

- [x] The acceptance-criteria scenario passes (forward fix + retrofit,
      verified live against the real vault)
- [x] Every Implementation Task above is complete (or explicitly dropped with
      reason)
- [x] All Constraints respected
- [ ] Automated tests added/updated and passing (once test tooling exists) —
      n/a, test tooling still pending; manual mode per Pipeline.md
- [x] `MEMORY.md` updated with any new decisions / patterns / constraints
- [x] `CHANGELOG.md` entry appended
- [x] `BUG-001` flipped `In Sprint → Closed` in both `BUGS.md` and
      `BACKLOG.md`'s `## Bugs` mirror once this story is `Done`

## Non-Goals / Out of Scope

- The not-yet-built Meeting→Attendees wikilink
  (`**Attendees:** [[Person1]], [[Person2]]`) — depends on `REQ-SB-08`
  (Meetings Capture Pipeline), which does not exist yet. Not part of this
  bug's scope; `BUG-001`'s repro and this fix are Email→Person only.
- Any other note-relationship direction beyond Email→Person — this fix does
  not re-audit every other entity relationship for the same gap (that
  broader audit, if the operator wants one, is separate forward work, not
  implied by this single-bug fix story).
- Redesigning the People or Email note schemas — both are already resolved
  (`Implementation/Plans/2026-08-10-vault-taxonomy-draft.md`); this story
  only adds the missing link, it does not touch any other field.

## Notes

**Prototype parity:** not applicable — this story has no screen surface.
`html-prototype/` was checked and contains no screen relevant to Email or
Person notes; this is backend/vault-content work only, same shape as
`REQ-SB-10-US-01` and `REQ-SB-14-US-01`.

**Why one scenario, not several:** per the triage-mode contract, one
untagged Gherkin scenario per bug in the batch — this batch is `BUG-001`
only. The scenario's `And` clauses (idempotent retrofit rerun, blank-
`sender_email` skip) are the same kind of edge-case coverage the original
`REQ-SB-10-US-01`/`REQ-SB-14-US-01` retrofits needed, folded into this one
scenario rather than split into separate ones, since they're all facets of
the same regression criterion ("the link exists, reliably, without side
damage") rather than independently valuable behaviours.

gate: clear 2026-08-11 — no triggers fired: no material assumption was
needed (the fix location, the two retrofit precedents, and the
non-destructive insert primitive to reuse are all already visible in the
existing code and already-Done stories, not guessed); `BUG-001` is a
finalised, non-`Draft` bug-ledger entry (trigger 2 doesn't apply — it's
scoped from `BUGS.md`, not an unfinalised PRD requirement); no ADR
created/changed (analyst scope); no `ESCALATIONS.md` entry needed; the story
is small and well-bounded (one existing call site to extend, one new
retrofit function mirroring two direct precedents) — not oversized; no
contradictory inputs between `BUGS.md`, `MEMORY.md`, and the live code; the
one detail left open (exact wikilink line format/placement) is a clean
architecture-level deferral with clear existing precedent to follow
(`**Customer:** [[Hub]]` / `**Company:** [[ADNOC]]`), not a genuinely
unclear or multiple-equally-valid choice.

---

**Architect pass (`/plan-tasks` step 1), 2026-08-11:**

**Architecture scope:** `Implementation/Architecture/architecture.md` →
Data Model → "Person Notes & Email-Sender Extraction (REQ-SB-10)" §
"Email → Person wikilink, the inbound direction (`BUGFIX-01`, closes
`BUG-001`)" (new bullet, just added) — this is the section the coder is
bounded by, plus the layer-boundary rule in § Source Layout (`api →
business → data_access`, ADR-003, unchanged) and the pre-existing
inline-body-wikilink convention in § "Customer Hub Notes & Graph Linking
(REQ-SB-14)" that this fix extends rather than replaces.

Concretely, the coder's scope per that section:
- **Forward fix — `app/business/email_classification.py`,
  `classify_recent_emails`:** capture the return value of the existing
  `people_extraction.ensure_person_note_for_captured_email(email["sender_name"],
  email["sender_email"])` call (currently discarded) into a variable, and
  — only when it is not `None` — call a new
  `people_extraction.link_email_to_person(note_path, person_result["note_path"])`.
  `note_path` (the just-written Email note's own path) is already in scope
  at that exact call site from the earlier `note_path =
  vault_writer.write_note(...)` line — no new plumbing. Do not change
  `ensure_person_note_for_captured_email`'s signature or behaviour.
- **New primitive — `app/business/people_extraction.py`:**
  `link_email_to_person(email_note_path, person_note_path) -> bool`,
  mirroring `customer_hub_linking.link_note_to_customer_hub`'s shape:
  derive the Person note's filename stem (`Path(person_note_path).stem`)
  and call `vault_writer.insert_body_line_if_missing(email_note_path,
  f"**Sender:** [[{stem}]]")`. Reuses the existing
  `insert_body_line_if_missing` primitive as-is — no `data_access` change
  needed. Note the existing `**Customer:** [[Hub]]` call on the same Email
  note (via `customer_hub_linking.ensure_hub_note_and_link`, already
  called earlier in `classify_recent_emails`) means this second insertion
  lands above it (both insert at the top of the body) — cosmetic, no AC
  depends on line order.
- **New retrofit — `app/business/people_extraction.py`:**
  `retrofit_email_sender_links()`, mirroring
  `retrofit_customer_hub_links`'s and `retrofit_people_from_emails`'s exact
  shape — iterate `vault_writer.list_all_note_paths()`; skip (status
  `skipped_no_sender_email`) a note with a blank/missing `sender_email`
  (Person/Customer-hub notes are skipped by construction, same as the
  existing retrofits); otherwise call `ensure_person_note(sender_name,
  sender_email)` (safe/idempotent even if `retrofit_people_from_emails`
  already ran) then `link_email_to_person(path, person_result["note_path"])`;
  record a `linked`/`already_linked` status per note, same result shape as
  the two existing retrofits.
- **New endpoint — `app/api/email_poc_router.py`:**
  `POST /poc/retrofit-email-sender-links`, matching the existing
  `/poc/retrofit-customer-hub-links` and `/poc/retrofit-people-from-emails`
  handler shape (call the retrofit, summarize counts, return `results`).
- **No `data_access` change needed** — `insert_body_line_if_missing`,
  `list_all_note_paths`, and `read_note` are all reused exactly as they
  already exist.

**ADR:** none created or changed. This is a direct application of the
already-`Accepted` inline-body-wikilink convention (no new tool, framework,
or structural boundary — `ADR-003`'s layering is unchanged, no new
cross-layer call shape, and the retrofit-endpoint pattern already has two
direct precedents) to a relationship direction (Email→Person) the original
`REQ-SB-10` architecture pass didn't check, per `MEMORY.md`'s 2026-08-11
standing constraint. Gate stays `clear` — no trigger 3, no assumption, no
contradiction with any `Accepted` ADR/PRD/`MEMORY.md` constraint found.

---

**Decomposer pass (`/plan-tasks` step 2), 2026-08-11:** The analyst's one
untagged scenario is split into three locked ACs, one per independently-
verifiable facet — `BUGFIX-01-US-01-AC-01` (the forward+backfilled
wikilink itself), `BUGFIX-01-US-01-AC-02` (retrofit idempotent rerun),
`BUGFIX-01-US-01-AC-03` (blank-`sender_email` skip, both paths) — tagged
in-place after each scenario's closing fence, mirroring the granularity
`REQ-SB-10-US-01`/`REQ-SB-14-US-01` already used for multi-clause
scenarios. No observable behaviour was changed from the analyst's draft;
wording tightened only for buildability (e.g. "matching that Person note's
own filename stem" made explicit).

Decomposed into two tasks per the architect's scope note, mirroring
`REQ-SB-10-US-01`'s task shape but collapsed to fit this bugfix's smaller
scope (no new `data_access` primitive is needed — `insert_body_line_if_missing`
already exists — so there is no separate "primitives" task):
`BUGFIX-01-US-01-T01` (the new `link_email_to_person` primitive in
`people_extraction.py`, plus wiring the existing-but-discarded
`ensure_person_note_for_captured_email` return value into it at
`email_classification.classify_recent_emails`'s call site — the forward/
going-forward half) and `BUGFIX-01-US-01-T02` (the new
`retrofit_email_sender_links` one-time batch, plus its
`POST /poc/retrofit-email-sender-links` endpoint — the backfill half).
`depends_on`: `T02 → [T01]` (the retrofit calls `link_email_to_person`,
added by T01) — acyclic, two tasks, no cycle possible.

Every locked AC has at least one AC-tagged manual verification step:
`AC-01` is split across both tasks (the going-forward half verified live
in T01 against the real Outlook/vault integration; the retrofit half
verified live in T02 against the real vault via the new endpoint) since
the scenario itself covers both paths; `AC-02` (retrofit idempotency) and
`AC-03` (blank-`sender_email` skip) are both verified live in T02 only —
mirroring `REQ-SB-10-US-01`'s own precedent of verifying its analogous
blank-`sender_email`-skip AC (`AC-09`) solely in its retrofit task, since
the skip guard is the same shared underlying code path for both the
going-forward hook and the retrofit, and the retrofit task is where a
blank-`sender_email` throwaway example is cheapest to construct.

Task `phase:` frontmatter omitted on both tasks — per Pipeline.md hard
rule 8, `BUGFIX-NN` stories (and, by the same reasoning, their tasks)
carry no `phase:`, since bug remediation is current work, not
roadmap-phased.

`status: Draft → Ready` — every AC is locked (3/3), every locked AC has a
tagged verification step, `depends_on` is acyclic across both tasks. Task
`status:` set to `Ready` in lockstep (written directly at `Ready` rather
than `Draft` then re-edited, since the story's advance to `Ready` in this
same pass was already determined before task authoring). `gate: clear
2026-08-11` (decomposer) — no MUST-FLAG trigger fired: no material
assumption beyond what the architect's already-recorded decisions settle
(the exact primitive shape, call-site edit, retrofit shape, and endpoint
were all specified verbatim in the architect's pass, not guessed);
`BUG-001` is finalised (not `<!-- Draft -->`); no ADR created/changed by
this step; no `ESCALATIONS.md` entry needed; decomposition is small and
well-bounded (two tasks, one new primitive + one call-site edit + one new
batch function + one new endpoint, each mirroring a direct existing
precedent) — not oversized; every locked AC is verifiable live against
the real vault; no contradictory inputs between the story, the architect's
notes, and the live code; the one task-shape judgement call (collapsing
what could have been three tasks — primitive, hook-wiring, retrofit+endpoint
— into two, since the primitive and the hook-wiring share one small edit
with no independent value split between them) has one clearly-better
answer given the architect's own scope note groups them together, not a
genuinely unclear/multiple-equally-valid choice.

---

**Coder pass (`/implement-sprint`), 2026-08-11:** Built T01 then T02 in
dependency order, exactly within each task's `## Files to Modify`, no
scope creep. All three locked ACs verified live against the real,
configured vault (`VAULT_PATH`): `BUGFIX-01-US-01-AC-01` (both the
going-forward half, confirmed via the real app-start capture writing
`**Sender:** [[rudra.potturu@tadweer.ae]]` into a genuinely newly
captured email, and the retrofit half, confirmed via
`POST /poc/retrofit-email-sender-links` linking a real pre-existing
Email note), `BUGFIX-01-US-01-AC-02` (a second retrofit run read
`already_linked` with no duplicate line), and `BUGFIX-01-US-01-AC-03` (a
naturally-occurring blank-`sender_email` note — `Work/Guides/Manual-
Entry-Guide.md` — was skipped, left byte-for-byte unchanged, no error).
Full detail in both tasks' Implementation Logs. The retrofit's one live
run linked 249 already-captured Email notes in one pass, closing the
entire backlog `BUG-001` described. No escalation, no blocker, no
`REVIEW-QUEUE.md`/`ESCALATIONS.md` entry needed — both tasks' judgement
calls (substituting natural vault examples for throwaway notes) were
already explicitly permitted by the story's own Context/Notes, not new
assumptions. `status: Ready → Done`.
