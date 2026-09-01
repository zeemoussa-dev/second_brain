---
id: REQ-SB-87-US-01-T06
title: Full regression verification across every already-Done template-driven note kind
parent_story: REQ-SB-87-US-01
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-01-T04, REQ-SB-87-US-01-T05]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-01-T06 — Full Regression Verification Across Every Already-Done Template-Driven Note Kind

## Parent Story

- Story: [[REQ-SB-87-US-01]] — `../UserStories/REQ-SB-87-US-01-vault-manager-resync-and-thread-templates.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Close out this story's own Scenario 5 with a real, comprehensive regression
pass — every already-`Done`, template-driven note kind must still be
found/created/updated correctly after `T01`-`T05`'s combined engine +
resync + retrofit + template changes, with zero regression.

---

## Starting State → End State

**Before / Inputs:**
- `T01`/`T02` extended the engine; `T03` resynced nine deployment copies;
  `T04` retrofitted `meeting-capture`/`create-companies-partners`'s own
  call sites; `T05` authored the new `thread`/`raw-message` template.
- Already-`Done`, template-driven note kinds in the real vault: Customer,
  Partner, Opportunity, Meeting, meeting-series, Note, File, plus
  `azure-kb-doc`/`compass-kb-doc`/`research-kb-doc`.

**After / Outputs:**
- A real, disclosed regression report confirming every one of those note
  kinds is still found/created/updated correctly through its own existing
  template and calling Skill — no regression to any already-`Done`
  capability.

---

## Files to Modify

- None — this task is verification-only, no new files.

---

## Constraints

- Inherits from parent story.
- Real evidence required, not "should still work" reasoning — run the full
  existing automated suite AND at least one real (or scratch, seeded from
  real) CLI invocation per already-migrated Skill (`meeting-capture`,
  `create-companies-partners`) that exercises its own real create/
  find/modify-section path.
- Never run more than one capture/write job concurrently against the same
  vault during verification (this codebase's own documented
  concurrent-write-race pitfall).

---

## Tests

**Manual verification steps:**
1. `[REQ-SB-87-US-01-AC-05]` Run the full `test_vault_manager.py` suite one
   final time (`src\backend\.venv\Scripts\python.exe -m pytest
   Hermes-Provisioning\shared\tests\test_vault_manager.py -v`) against the
   fully-extended engine (`T01`+`T02`); confirm 100% pass, including every
   pre-existing test.
2. `[REQ-SB-87-US-01-AC-05]` Run `ingest_meeting.py` (real or scratch,
   seeded from real) end-to-end once more, post-`T04`'s retrofit AND
   post-`T03`'s resync of its own deployed copy; confirm Meeting/
   meeting-series creation and section writes are unchanged from their
   real, already-`Done` shape.
3. `[REQ-SB-87-US-01-AC-05]` Run `create_companies_partners.py` (real or
   scratch) end-to-end once more, post-`T04`'s retrofit; confirm Customer/
   Partner/Affiliate creation, tagging, and log/captures children are
   unchanged from their real, already-`Done` shape.
4. `[REQ-SB-87-US-01-AC-05]` Spot-check one real note of each of the
   remaining already-`Done`, template-driven kinds this story's own
   Scenario 5 names (Opportunity, Note, File, `azure-kb-doc`,
   `compass-kb-doc`, `research-kb-doc`) via `vault_manager.py find`/
   `get-section` CLI calls against the real, live vault; confirm each is
   still found and its own declared sections still read correctly.
5. `[REQ-SB-87-US-01-AC-01]` Re-confirm all nine deployment copies remain
   byte-identical to the canonical source at the close of this story (no
   drift reintroduced by `T04`'s edits, which touch the CALLING scripts,
   never the engine copy itself).

**Automated tests:** the pytest command in step 1 above.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Every already-`Done` template-driven note kind is confirmed
      regression-free
- [x] The full `test_vault_manager.py` suite passes 100%
- [x] All nine deployment copies remain byte-identical
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any new capability — this task only verifies what `T01`-`T05` already
  built.
- `email-thread-capture`/`summarize-and-tag-threads` real migration
  verification — `REQ-SB-87-US-02`/`REQ-SB-87-US-04`'s own scope (this
  story's own new templates are proven generically here and end-to-end via
  `T05`'s own automated Thread-template tests; the actual SCRIPTS that will
  consume them are sibling stories).

---

## Context / Notes

This is the closing task for `REQ-SB-87-US-01` — once all 5 locked ACs
verify clean here, the story's own Definition of Done is satisfied for
everything within this story's own `## Files to Modify` scope.

---

## Implementation Log

**What was changed:** nothing — verification-only, per this task's own
`## Files to Modify` (none). All five numbered `## Tests` steps run live
against real, unmodified code (the canonical, fully-resynced engine and
both already-`Done` calling scripts), never a mock.

**Step 1 — full `test_vault_manager.py` suite (`AC-05`):**
```
src\backend\.venv\Scripts\python.exe -m pytest Hermes-Provisioning\shared\tests\test_vault_manager.py -v
```
**PASS — 52/52** (44 pre-existing + `T01`'s 6 dynamic-children tests +
`T02`'s 2 per-caller-access tests, all passing, zero regressions).

**Step 2 — `ingest_meeting.py` end-to-end, post-`T03`/`T04` (`AC-05`):**
real, unmodified `ingest_meeting()` (direct import, no CLI subprocess)
driven against a fresh scratch vault seeded with the REAL, current
`meeting`/`meeting-series` `Template.json` files copied from the live
vault. Ran a one-time meeting and a two-occurrence recurring series (same
real Outlook-EntryID-collision scenario the series/occurrence dedup logic
must survive). A thin spy wrapped around `vm.create`/`vm.modify_section`
recorded every real call's own `caller` kwarg. **PASS**: all 6 real
`create`/`modify_section` calls fired carried `caller="ingest_meeting"`;
one-time meeting note created correctly; series concept note + both
occurrence notes created correctly, occurrence 2's own `bump_folder_date`
call correctly moved the series folder (and its nested Recurrences/
children) forward, re-resolved via `find_by_id` post-move (never trusting
the earlier, now-stale result-dict paths); `## History` held both real
occurrence wikilinks, never the one-time meeting's; both occurrence notes
carried `calendar_event_id` in frontmatter. Zero output-shape deviation
from `T04`'s own already-recorded real shape. Scratch vault deleted after.

**Step 3 — `create_companies_partners.py` end-to-end, post-`T04` (`AC-05`):**
real, unmodified `build()` driven against a fresh scratch vault seeded
with the REAL, current `customer`/`partner` `Template.json` files,
against a scratch `Entities.md` naming a top-level Customer ("Zeta
Holdings") and an Affiliate ("Zeta Robotics") whose parent ("Zeta
Parentco") did not yet exist — exercising all 3 real `vm.create` call
sites in one run (top-level Customer, auto-created Affiliate-of parent,
Affiliate). **PASS**: all 3 real calls carried
`caller="create_companies_partners"`; the auto-created parent note
existed and its own `## Affiliates` section named the Affiliate by its
real stem (the link-back); the Affiliate note was correctly nested under
the parent's own `Affiliates/` folder; the top-level Customer's own
frontmatter carried its real domain and both `-log.md`/`-captures.md`
fixed children existed; `Entities.md` was rewritten with `Created: Yes`
for the real entries. Scratch vault deleted after.

**Step 4 — spot-check the remaining already-`Done` template-driven kinds
against the REAL, live vault (`AC-05`):** used `vault_manager.py find`
(CLI) plus a direct call to the real, unmodified `get_section_content()`
(the underlying function `get-section`'s own CLI wrapper calls — its CLI
form only accepts `--id`, narrower than the real function it wraps, which
also takes a resolved path directly; used here to reach notes whose real
frontmatter predates the `id`-based identity convention, without touching
any file). All 6 named kinds found and read correctly against real,
existing vault content:
- **Opportunity** — `find --by id` on a real Opportunity's own real `id`
  resolved its real path; `get-section Summary` returned its real content.
- **Note** — `find --by filename` on a real, ENGINE-created Note
  (`Work/Notes/2026-08-23/Line one.md`) resolved correctly (scoped
  correctly under the engine's own `Work/` search root — a same-named
  `type: "Note"` HAND-WRITTEN note living outside `Work/`,
  `Personal/Initiatives/...`, is correctly NOT found by the engine's
  `Work/`-scoped `find`, since it was never created through this
  template; a second false lead, some `type: "Note"` files under
  `Work/Initiatives/Sherif Tawfik Second Brain/` predate the engine
  entirely and carry no `## Summary`/`## Body` headers at all — disclosed
  below, not a regression); `get_section_content` returned real
  `## Summary`/`## Body` content for the genuine engine instance.
- **File** — `find --by filename` resolved a real captured File note;
  `get_section_content` returned real `## Summary`/`## Details` content.
- **azure-kb-doc** / **compass-kb-doc** / **research-kb-doc** — same
  `find --by filename` + `get_section_content` pattern against one real
  note of each kind; all resolved and read correctly.

(Disclosed, non-blocking finding: the CLI's own `get-section` subcommand
only accepts `--id`, not `--by`/`--value` — narrower than the underlying
`get_section_content(path, section)` function, which takes any resolved
path. Not a regression (identical to `T05`'s already-disclosed CLI-vs-
function-surface note) — used the real function directly against a real,
`find`-resolved path, per this codebase's own established "direct-import
verification" precedent, not a CLI limitation worked around by editing
any file.)

**Step 5 — re-confirm all nine (82 real) deployment copies remain
byte-identical (`AC-01`):** SHA-256 checksum of the canonical
`Hermes-Provisioning/shared/vault_manager.py` against all 9 repo copies
and all 73 real, active Hermes profile copies. **PASS — all 82 match the
canonical hash exactly** (`9b9caff1...e83c34af9`, the SAME hash `T03`
recorded at close) — confirms `T04`'s edits (the two CALLING scripts
only) introduced zero drift to the engine copy itself.

**Bonus, not a locked-AC requirement — one combined scratch-vault pass
exercising `T01`/`T02`/`T05` together, plus an unrelated already-`Done`
kind, in the SAME process:** created a real Thread (`thread` template)
with 3 real, distinct `growth: "dynamic"` RawMessage children under its
own `messages/` folder, confirmed `## Related` succeeds for
`link_person_to_thread` and refuses `capture_attachments`, then created a
real Meeting note in the exact same running process right after —
confirming zero shared-state interference between the brand-new Thread/
dynamic-children machinery and an unrelated, already-`Done` note kind
sharing the same canonical engine instance. All assertions passed.

**Full script output (all 4 live verification scripts, concatenated):**
```
pytest: 52 passed in 0.70s
ingest_meeting: ALL_CALLS_CARRY_INGEST_MEETING_CALLER=True; series/occurrence/
  one-time shapes all correct post-bump_folder_date re-resolution
create_companies_partners: ALL_CALLS_CARRY_CCP_CALLER=True; customer/parent/
  affiliate/back-link/log-captures/Entities.md-rewrite all correct
spot-checks: Opportunity/Note/File/azure-kb-doc/compass-kb-doc/research-kb-doc
  all found + real section content read correctly
sync re-check: 82/82 real deployed copies byte-identical to canonical (SHA-256)
combined pass: Thread+3 RawMessage children+caller-access+Meeting, same
  process, zero interference
```

**Verification outcomes keyed by AC-ID:**
- `[REQ-SB-87-US-01-AC-01]` **PASS** — re-confirmed live (step 5): all 82
  real deployed copies remain byte-identical to the canonical source; no
  drift reintroduced by `T04`.
- `[REQ-SB-87-US-01-AC-05]` **PASS** (steps 1-4, all four sub-steps) —
  every already-`Done` template-driven note kind (Customer, Partner,
  Opportunity, Meeting, meeting-series, Note, File, azure-kb-doc,
  compass-kb-doc, research-kb-doc) is confirmed regression-free through
  its own real template and calling Skill, with zero regression.

**No `ESCALATIONS.md` / `REVIEW-QUEUE.md` entries written by this task**
— no new dependency, no shared-interface change, no ADR deviation, no
unanticipated file (verification-only, `## Files to Modify` is empty and
stayed empty), and both locked ACs verified live with a real positive
result. The disclosed findings above (the Note-kind false-lead, the
narrower `get-section` CLI surface) are scope-internal verification-
technique notes for human spot-check, not material assumptions filling a
requirement gap — no `MEMORY.md` entry warranted (nothing here is a new
decision/pattern/constraint beyond what `T01`-`T05` already recorded;
`CHANGELOG.md` gets a closing entry for the sprint/story's own
completion instead).

gate: clear 2026-09-01 — no triggers fired (verification-only, zero code
changed; every locked AC verified live with a real positive result across
all five numbered Tests steps plus a bonus combined pass; no ESCALATIONS
entry; task not oversized; no ADR deviation).
