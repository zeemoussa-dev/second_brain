---
id: REQ-SB-87-US-01-T04
title: Retrofit meeting-capture / create-companies-partners callers for the new caller-identity argument
parent_story: REQ-SB-87-US-01
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-01-T03]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-01-T04 — Retrofit meeting-capture / create-companies-partners Callers for the New Caller-Identity Argument

## Parent Story

- Story: [[REQ-SB-87-US-01]] — `../UserStories/REQ-SB-87-US-01-vault-manager-resync-and-thread-templates.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Update every real, already-`Done` mutating call site in `ingest_meeting.py`
(`meeting-capture`) and `create_companies_partners.py`
(`create-companies-partners`) to pass its own stable caller-identity
argument on every `vm.create()`/`vm.modify_section()` call — per `ADR-017`'s
own Consequences ("every mutating caller across every already-migrated
Skill... must now pass its own stable caller-identity argument... a small,
mechanical signature change with real retrofit surface across already-Done
code").

---

## Starting State → End State

**Before / Inputs:**
- `T02`'s new `caller` parameter defaults to `None`/omittable, so these
  call sites keep working unchanged even without this task — but the ADR
  explicitly names this retrofit as required so the whole system
  consistently declares caller identity going forward (future-proofing
  against a later `allowed_callers` declaration on either Skill's own
  templates).
- Confirmed real call sites (direct read, 2026-09-01):
  - `ingest_meeting.py`: `vm.create(...)` at line ~103 (series),
    ~176 (occurrence), `vm.modify_section(...)` at line ~194, `vm.create(...)`
    at line ~218.
  - `create_companies_partners.py`: `vm.create(...)` at line ~828 (top-level
    Customer/Partner), ~868 (auto-created Affiliate-of parent), ~889
    (Affiliate).

**After / Outputs:**
- Every one of those call sites passes an explicit `caller=` argument
  identifying its OWN script (a stable, self-declared string — e.g.
  `caller="ingest_meeting"` for every call in `ingest_meeting.py`,
  `caller="create_companies_partners"` for every call in
  `create_companies_partners.py`). One identity string per SCRIPT (not per
  call site within it), matching the trust boundary `ADR-017`'s own
  Consequences describe ("a caller identity is a bare, self-declared string
  the engine trusts... every real caller today is this project's own
  first-party code").
- No `Template.json` for either Skill's own note kinds (Meeting,
  meeting-series, Customer, Partner, Affiliate) gains an `allowed_callers`
  declaration in this task — none is needed or requested; this is purely
  the mechanical signature retrofit, with zero behavior change (every
  section they write remains open to any `machine_write` caller).

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/meeting-capture/scripts/ingest_meeting.py`
- `Hermes-Provisioning/skills/company-review/create-companies-partners/scripts/create_companies_partners.py`

---

## Constraints

- Inherits from parent story.
- **Never weaken any already-established section-ownership guard** — this
  is a pure retrofit (adding an argument), not a behavior change; every
  already-`Done` write must still succeed exactly as before.
- One stable identity string per script, reused across every call site
  inside that same script — never a different string per call.
- Do not add any `allowed_callers` declaration to Meeting/Customer/
  Partner/Affiliate's own `Template.json` files in this task — out of
  scope, not requested.

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-01-AC-05]` (real-vault regression, `meeting-capture`)
   Run `ingest_meeting.py` against a real (or scratch, seeded from real)
   meeting capture already known to exercise its series/occurrence/section
   paths; confirm every one of its own `vm.create`/`vm.modify_section`
   calls now passes `caller=` and still succeeds with the SAME real
   frontmatter/section output as before this retrofit — no regression to
   Meeting/meeting-series capture.
2. `[REQ-SB-87-US-01-AC-05]` (real-vault regression,
   `create-companies-partners`) Run `create_companies_partners.py` against
   a real (or scratch) input that exercises a top-level Customer/Partner
   create, an auto-created Affiliate-of parent, and an Affiliate create;
   confirm every call now passes `caller=` and still succeeds identically
   — no regression to Customer/Partner/Affiliate capture.
3. (Unlabeled, supporting) Confirm neither script's own real output
   (printed JSON, file frontmatter/body shape) changed in any way other
   than the internal `caller=` argument — a pure mechanical retrofit.

**Automated tests:** `n/a — Skill scripts have no existing pytest harness;
verified via real/scratch-vault CLI runs, per this codebase's own
established pattern for this file family`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Every `vm.create`/`vm.modify_section` call in `ingest_meeting.py`
      passes `caller="ingest_meeting"`
- [x] Every `vm.create`/`vm.modify_section` call in
      `create_companies_partners.py` passes
      `caller="create_companies_partners"`
- [x] Both scripts' own real, already-`Done` output is unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any change to either script's own real business logic (recurrence
  computation, company auto-create, affiliate resolution).
- Declaring `allowed_callers` on any Meeting/Customer/Partner/Affiliate
  template — not requested.
- `email-thread-capture`'s own scripts (`REQ-SB-87-US-02`) or
  `summarize-and-tag-threads`'s own script (`REQ-SB-87-US-04`) — different
  Skills, own stories, own new (first-time) caller-identity wiring.

---

## Context / Notes

`ADR-017`'s own Consequences section is the authoritative source for why
this retrofit is required even though it's not strictly enforced by any
`allowed_callers` declaration today. Confirm the real, current line numbers
of each call site directly in the file before editing — this task's own
line-number references above are from a direct 2026-09-01 read and may have
shifted slightly by build time.

---

## Implementation Log

**Real, current call-site inventory re-confirmed directly (2026-09-01,
before editing — line numbers had shifted slightly from the task's own
prose, per its own Context note):**
- `ingest_meeting.py`: `vm.create` (series, line ~103), `vm.create`
  (occurrence, line ~176), `vm.modify_section` (`History`, line ~194),
  `vm.create` (one-time meeting, line ~218) — 4 call sites, matching the
  task's own count exactly.
- `create_companies_partners.py`: `vm.create` (top-level Customer/
  Partner, line ~828), `vm.create` (auto-created Affiliate-of parent, line
  ~868), `vm.create` (Affiliate, line ~889) — 3 call sites, zero
  `vm.modify_section` calls in this file (confirmed by grepping the whole
  file, not just the task's own named lines).

**What was changed:**
- `ingest_meeting.py`: added module constant `_VM_CALLER = "ingest_meeting"`
  and `caller=_VM_CALLER` on all 4 real call sites above. No other line
  touched.
- `create_companies_partners.py`: added module constant
  `_VM_CALLER = "create_companies_partners"` (next to the existing
  `_CUSTOMER_TEMPLATE_ID`/`_PARTNER_TEMPLATE_ID` constants) and
  `caller=_VM_CALLER` on all 3 real call sites above. No other line
  touched.
- Confirmed via `create()`'s/`modify_section()`'s own real signatures
  (`Hermes-Provisioning/shared/vault_manager.py`, both files' own resynced
  copy, `T03`) that `caller: str | None = None` is already a real,
  deployed keyword parameter on both functions — this task added no
  engine change, purely caller-side.

**Live verification (real scratch vault, seeded from the real
`meeting`/`meeting-series`/`customer`/`partner` `Template.json` files
copied from the actual live vault at `VAULT_PATH`; deleted after
verification, not a repo artefact). Both scripts were driven via their
OWN, real, unmodified functions (direct import, no CLI subprocess) with a
thin, scoped spy wrapped around `vm.create`/`vm.modify_section` that
records each real call's own `caller` kwarg before delegating to the real,
unmodified implementation underneath — never a mock of the write path
itself:**

`[REQ-SB-87-US-01-AC-05]` (real-vault regression, `meeting-capture`) —
**PASS.** Ran the real `ingest_meeting()` three times against the scratch
vault: a recurring series' first occurrence (creates the series concept
note + the first occurrence — 2 `create` calls + 1 `History`
`modify_section` call), the same series' second occurrence one week later
(creates a second occurrence under the series, now correctly re-nested
after `bump_folder_date` moved the series folder forward — 1 `create`
call + 1 `History` `modify_section` call, confirming today's real
Outlook-EntryID-collision dedup key still worked unchanged), and a
one-time meeting (1 `create` call). All 6 real `vm.create`/
`vm.modify_section` calls fired carried `caller="ingest_meeting"`
(confirmed via the spy's own recorded log). Read every written note back
from disk directly: series concept note's `## History` held both real
occurrence wikilinks in order, occurrence/one-time notes carried the
correct `start`/`end`/`organizer`/`calendar_event_id`/`calendar_series_id`
frontmatter and section scaffold (`## Summary`/`## Quick Notes`/
`## Related`/`## Personal Notes`/`## Actions`, `## History` additionally
on the series note) — the exact same shape `T03`'s own no-`--caller`
smoke test already established for this file family, confirming zero
output regression.

`[REQ-SB-87-US-01-AC-05]` (real-vault regression,
`create-companies-partners`) — **PASS.** Ran the real `build()` against a
scratch `Entities.md` naming a top-level Customer ("Acme Corp", no
`Affiliate of`), and an Affiliate ("Acme Subsidiary") whose named parent
("Acme Parent Not Yet Created") did not yet exist — exercising all 3 real
call sites in one run: the top-level Customer create, the auto-created
Affiliate-of-parent create, and the Affiliate create (`parent_value=`).
All 3 real `vm.create` calls fired carried
`caller="create_companies_partners"` (confirmed via the spy's own
recorded log). Read every written hub/affiliate note back from disk
directly: correct `type`/`name`/`domain`/`affiliate_of`/`tags`
frontmatter, correct `## Affiliates`/`## Log & Captures` section
scaffold, and the auto-created parent's own "## Affiliates" back-link to
the Affiliate note present — the parent-auto-create/`_child_note_name`/
link-back mechanics fired unchanged, matching the shape this file's own
already-`Done` capability already produced before this retrofit.

(Unlabeled, supporting) Confirmed both scripts' own real output (the
returned result dict's own keys/values, and every written file's
frontmatter/section content) is unchanged in every respect other than the
internal `caller=` argument now present on each call — a pure mechanical
retrofit, no business-logic line touched in either file.

**Scope-internal note (disclosed, non-blocking):** this task's own
`## Files to Modify` names only the two `Hermes-Provisioning/` repo
script paths — unlike `T03`, it does not name any real, active Hermes
profile deployment copy of `ingest_meeting.py`/`create_companies_
partners.py`. Per `[[feedback_deploy_hermes_provisioning_manually]]`, the
repo edit alone is inert in production until manually deployed; not done
here, since it is outside this task's own authored `## Files to Modify`
scope (staying within scope per the coder's own hard rule, not silently
expanding it). This has **zero real runtime consequence today**: `T02`/
`T03` already confirmed live that no real `Template.json` in the live
vault declares `allowed_callers` for Meeting/meeting-series/Customer/
Partner/Affiliate, so the deployed (pre-retrofit) copies of these two
scripts continue to behave identically to the retrofitted repo copies
until/unless a future template restricts one of their own sections.
Flagged here for visibility, not filed as an `ESCALATIONS.md`/
`REVIEW-QUEUE.md` item — it is a reasonable, disclosed reading of the
task's own unambiguous `## Files to Modify` list, not an assumption
filling a requirement gap.

**No `ESCALATIONS.md` / `REVIEW-QUEUE.md` entries written by this task**
— no new dependency, no shared-interface change beyond what `ADR-017`
already governs, no ADR deviation, no unanticipated file, and both
AC-tagged verification steps (plus the unlabeled supporting step) verified
live with a real positive result.

gate: clear 2026-09-01 — no triggers fired (ADR-017 already governs this
task's own scope; the one scope-internal note above is a disclosed,
non-blocking reconciliation against the task's own unambiguous `## Files
to Modify` list, not an assumption filling a requirement gap; no
ESCALATIONS entry; task not oversized; the locked AC verified live with a
real positive result across both real callers).
