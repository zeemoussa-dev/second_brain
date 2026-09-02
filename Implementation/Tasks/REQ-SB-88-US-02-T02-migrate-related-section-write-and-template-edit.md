---
id: REQ-SB-88-US-02-T02
title: Migrate ## Related section write; resolve the per-caller access-guard question
parent_story: REQ-SB-88-US-02
requirement_id: REQ-SB-88
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-88-US-02-T01]
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-02-T02 — Migrate ## Related Section Write; Resolve the Per-Caller Access-Guard Question

## Parent Story

- Story: [[REQ-SB-88-US-02]] — `../UserStories/REQ-SB-88-US-02-track-opportunities-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-88 *Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking*

---

## Objective

Migrate `link_opportunity()`'s own `## Related` section write onto
`vault_manager.py`'s public, template-driven `vm.modify_section`, making the
ONE real Template.json data edit this requires for the Thread case, and
retire the now-fully-superseded local write primitives/guard.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `link_opportunity.py`: appends `[[<Opportunity title>]]`
  to the target note's `## Related` section via the local
  `insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section(note_path, "## Related", ..., caller=
  _RELATED_CALLER)`, gated by its own local `_CALLER_ALLOW_LISTS =
  {_RELATED_CALLER: frozenset({"## Related"})}`.
- **Real, confirmed access-control gap (architect finding, this
  session):** the real, deployed Thread Template.json's `## Related`
  section currently declares `"allowed_callers": [
  "link_person_to_thread"]` (`ADR-017`) — a migrated `vm.modify_section`
  call with `caller="link_opportunity"` would be REFUSED outright for a
  Thread target unless `link_opportunity` is added to that same array.
  The real, deployed Meeting Template.json's `## Related` section carries
  **no `allowed_callers` key at all** (open to any machine-write caller
  today) — confirmed directly, zero edit needed for the Meeting case.
- **Resolved implementation-shape question (architect, this session):**
  the already-public `vm.modify_section` entry point is sufficient — no
  reach into underscore-private helpers (`_set_section_content`), and
  nothing needs promoting to public. It resolves the target purely by
  `note_id` (the same path `apply_thread_review.py` already uses); the
  script mints/reads that `id` via `vm.update` exactly like the Thread-
  migration precedent, plus picks which template to load (`"thread"` vs
  `"meeting"`), trivially derivable from `note_path`'s own
  `Work/Threads/` vs `Work/Meetings/` prefix.

**After / Outputs:**
- `Templates/thread/Template.json`'s `## Related` section
  `allowed_callers` becomes `["link_person_to_thread",
  "link_opportunity"]` — additive, `link_person_to_thread` preserved. The
  Meeting Template.json needs zero edit.
- `link_opportunity()` now: (1) derives `template_id = "thread"` or
  `"meeting"` from `note_path_str`'s own `Work/Threads/`/`Work/Meetings/`
  prefix; (2) loads that template via `vm.load_template`; (3) reads the
  note's own real frontmatter `id` via `vm.read_note(note_path)`, minting
  and persisting a fresh `uuid4()` via `vm.update(...)` the first time a
  note with no `id` is touched (same pattern `T01`/`REQ-SB-87-US-04-T01`
  already established); (4) writes `## Related` via
  `vm.modify_section(vault_path, template, section="Related",
  content=<rebuilt line list with the wikilink appended if missing>,
  mode="replace", note_id=<id>, caller="link_opportunity")`.
- `_RELATED_CALLER`/`_CALLER_ALLOW_LISTS` and the local
  `insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section` are removed once `T01`'s frontmatter migration
  plus this task's `## Related` migration leave them with zero remaining
  callers (confirm by re-reading the whole file before removing —
  mirrors `REQ-SB-87-US-04-T03`'s own precedent). The real restriction on
  who may write `## Related` is now enforced SOLELY by the Thread
  template's own `allowed_callers` declaration (for Thread targets) —
  never a silent widening, since the equivalent restriction now lives in
  Template.json instead of local Python.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/track-opportunities/scripts/link_opportunity.py`
- `C:/myWorx/Moussa MD/Moussa Brain/.second-brain/data/Templates/thread/Template.json` (real, live deployed template — add `link_opportunity` to `## Related`'s `allowed_callers`)

---

## Constraints

- Inherits from parent story.
- `link_person_to_thread`'s own existing `allowed_callers` entry on the
  Thread's `## Related` must remain — additive edit only.
- Meeting's `## Related` template is left untouched (already open,
  confirmed live — zero edit needed there).
- Zero behavior change to any already-working write path beyond WHO the
  access check is enforced by — this task does not change WHAT gets
  written to `## Related`.
- Verify against a scratch vault, distinct `--vault-path`.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
`thread`/`meeting` Template.json files copied byte-identical from the
real, live vault — including this task's own `## Related` `allowed_callers`
edit applied to the SCRATCH Thread template copy first):**

1. `[REQ-SB-88-US-02-AC-02]` Given the same scratch Thread or Meeting note
   from `T01`'s own `AC-01` run, now linked once, re-run
   `link_opportunity.py` for the SAME Opportunity; confirm the note's own
   `## Related` section already lists the Opportunity's wikilink and is
   left unchanged — `linked` is reported `false`, no duplicate line added.
   Confirm the `opportunities` frontmatter list is likewise unchanged (no
   duplicate wikilink entry). Run once each against a Thread target AND a
   Meeting target to prove both template paths (Thread requiring the new
   `allowed_callers` entry; Meeting requiring none).
2. (Unlabeled, supporting) Attempt (via a disposable throwaway script, not
   this Skill's own entry point) a `## Related` write on the SAME scratch
   Thread with `caller="some_other_script"`; confirm it is refused with a
   real `VaultManagerError`, and that a write with
   `caller="link_opportunity"` succeeds — confirms the Template.json edit
   is genuinely load-bearing. Confirm a `caller="link_person_to_thread"`
   write to the same section STILL succeeds (the pre-existing caller is
   preserved, not silently dropped).
3. (Unlabeled, supporting) Confirm the local `_RELATED_CALLER`/
   `_CALLER_ALLOW_LISTS`/`insert_body_section_if_missing`/
   `read_body_section`/`replace_body_section` are no longer present as
   live code in the finished file (or, if any name is kept for a real,
   disclosed reason, confirm it is no longer load-bearing for access
   control).

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `link_opportunity` added to the real, deployed Thread Template.json's
      `## Related` `allowed_callers` (additive, `link_person_to_thread`
      preserved); Meeting template confirmed to need no edit
- [x] `## Related` write migrated onto `vm.modify_section`, template
      derived correctly from `Work/Threads/` vs `Work/Meetings/` prefix
- [x] Idempotent re-run (same Opportunity) leaves both `## Related` and
      `opportunities` frontmatter unchanged, `linked: false`
- [x] Local `_CALLER_ALLOW_LISTS`-based guard fully retired; access now
      enforced solely by `vault_manager.py`'s template-declared control
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `opportunities` frontmatter write — `T01`.
- Real-vault retrofit verification — `T03`.
- Any change to `resolve_opportunity()`/ambiguity handling.

---

## Context / Notes

`architecture.md` → `§track-opportunities Link-Write Migration
(REQ-SB-88-US-02)` is authoritative on both the Template.json edit and
the "public `modify_section` is sufficient, no private-helper reach"
resolution. The live Template.json path is outside the repo — edit it
directly at its real, deployed location, then verify the SCRATCH vault's
own copy carries the same edit before running any scratch-vault test.

---

## Implementation Log

**2026-09-02, coder.** Edited the real, live `Templates/thread/
Template.json`'s `## Related` section, adding `link_opportunity` to
`allowed_callers` alongside the pre-existing `link_person_to_thread`
(additive, confirmed by direct read before/after). Confirmed the real,
live Meeting `Template.json`'s `## Related` section carries no
`allowed_callers` key at all — zero edit made there, per the architect's
own finding. Migrated `link_opportunity()`'s `## Related` write onto the
already-public `vm.modify_section` (`caller="link_opportunity"`), adding
`_template_id_for_note()` to derive `"thread"`/`"meeting"` from the
target note's own real `Work/Threads/`/`Work/Meetings/` path prefix (no
reach into any underscore-private helper, matching the architect's own
resolution). id-mint-if-missing mirrors `T01`/`REQ-SB-87-US-04-T01`'s
own precedent. Removed the now-fully-dead local `_RELATED_CALLER`/
`_CALLER_ALLOW_LISTS` guard and the local `insert_body_section_if_missing`/
`read_body_section`/`replace_body_section`/`_format_frontmatter_value`
primitives after confirming zero remaining callers by re-reading the
whole file. `resolve_opportunity()`/`_iter_opportunity_notes()` and the
local `read_note` (still used by `resolve_opportunity`) untouched.

**Verification (same scratch vault as `T01`,
`.second-brain/data/Templates/thread/Template.json` re-copied from the
real, live vault including this task's own `## Related` edit; a second
scratch Opportunity `Expansion Q4` under Acme Corp added to force a
genuinely NEW `## Related` write distinct from `T01`'s own already-linked
`Renewal 2026`):**

- `[REQ-SB-88-US-02-AC-02]` **PASS (Thread target).** Re-ran
  `link_opportunity.py` against Thread B for the SAME Opportunity
  (`Renewal 2026`, `--customer "Acme Corp"`, already linked by `T01`'s
  own run): `linked: false`, `## Related` and `opportunities`
  frontmatter both byte-unchanged, no duplicate wikilink. Then ran
  against Thread B for a GENUINELY NEW Opportunity (`Expansion Q4`):
  `linked: true`; confirmed on disk `opportunities` gained
  `"[[Expansion Q4]]"`, `## Related` gained a new `- [[Expansion Q4]]`
  line (the pre-existing `- [[Renewal 2026]]` line preserved, not
  overwritten), and a fresh Thread `id` was minted/persisted
  (`f7f16b46-469c-4f5a-a81e-5c4f50605c66` — this scratch Thread had never
  been touched by any id-minting migrated caller before). This proves the
  MIGRATED `vm.modify_section` path (not just the pre-existing line)
  genuinely executed and was accepted against the newly-widened
  `allowed_callers`.
  **PASS (Meeting target).** Ran `link_opportunity.py` against Meeting B
  for `Renewal 2026`: `linked: true`, `opportunities`/`## Related` both
  gained the wikilink, a fresh Meeting `id` minted — the Meeting
  template's own `## Related` (no `allowed_callers` key) accepted the
  write with zero Template.json edit, confirming the architect's own
  finding. Re-ran the identical call: `linked: false`, byte-unchanged —
  idempotent for the Meeting path too.
- (Unlabeled, supporting) **PASS.** A disposable throwaway script called
  `vm.modify_section(..., section="Related", ..., caller=
  "some_other_script")` directly against the scratch Thread — refused
  with a real `VaultManagerError` ("section 'Related' in template
  'thread' only allows ['link_person_to_thread', 'link_opportunity'] to
  write it -- caller 'some_other_script' is refused"). The SAME call with
  `caller="link_person_to_thread"` (the pre-existing caller) still
  succeeded — confirms it was preserved, not silently dropped. The SAME
  call with `caller="link_opportunity"` also succeeded.
- (Unlabeled, supporting) **PASS.** Confirmed by direct `grep` that
  `_RELATED_CALLER`/`_CALLER_ALLOW_LISTS`/`insert_body_section_if_missing`/
  `read_body_section`/`replace_body_section` no longer appear anywhere in
  the finished file.

**Assumptions (scope-internal, for human spot-check):** the second
scratch Opportunity (`Expansion Q4`) was added specifically to force a
genuinely new write through the migrated path, beyond what `T01`'s own
already-linked fixture alone would exercise — a deliberate strengthening
of this task's own verification, not a deviation from its Tests block.

gate: clear 2026-09-02 — no MUST-FLAG trigger fired (the one locked AC
this task owns verified live with a real positive result across both
Thread and Meeting targets, the Template.json edit matches the
architect's own already-resolved finding exactly, no new dependency/
interface change, no ADR touched).
