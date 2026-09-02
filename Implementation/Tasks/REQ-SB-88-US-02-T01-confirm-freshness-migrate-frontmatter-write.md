---
id: REQ-SB-88-US-02-T01
title: Confirm deployed vault_manager.py freshness; migrate opportunities-frontmatter write
parent_story: REQ-SB-88-US-02
requirement_id: REQ-SB-88
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: []
created: 2026-09-02
updated: 2026-09-02
---

# REQ-SB-88-US-02-T01 — Confirm Deployed vault_manager.py Freshness; Migrate opportunities Frontmatter Write

## Parent Story

- Story: [[REQ-SB-88-US-02]] — `../UserStories/REQ-SB-88-US-02-track-opportunities-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-88 *Close the Remaining `vault_manager.py` Migration Gaps — Attachment Summarization + Opportunity Linking*

---

## Objective

Reconfirm the already-deployed `track-opportunities/scripts/vault_manager.py`
copy is byte-current against the canonical source, then migrate
`link_opportunity()`'s own `opportunities` frontmatter-list write onto it.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `link_opportunity.py` (229 lines, read directly this
  session): `link_opportunity()` reads the target note's frontmatter via
  the local `read_note`, appends `[[<Opportunity title>]]` to its
  `opportunities` list (if not already present) via a hand-rolled
  frontmatter-line rewrite (`_format_frontmatter_value`/direct line
  splice), never imports `vault_manager.py` at all.
- `track-opportunities/scripts/vault_manager.py` already exists — a real,
  deployed copy confirmed byte-current against the canonical
  `Hermes-Provisioning/shared/vault_manager.py` as of `REQ-SB-87-US-01`'s
  own resync — but this task must independently RECONFIRM that freshness
  (a direct diff), not assume it still holds, before building against it.

**After / Outputs:**
- Freshness reconfirmed via direct diff; if real drift is found (not
  expected — resync it from the canonical source first, then proceed —
  a real, disclosed deviation from "just build," logged in the
  Implementation Log).
- `link_opportunity()`'s `opportunities` frontmatter-list write migrates
  onto `vm.read_note(note_path)` (read the existing list) +
  `vm.update(vault_path, note_path, frontmatter={"opportunities":
  merged_list})` — the same shape `apply_thread_review.py`'s own
  frontmatter stamping already uses. No `note_id`/template/`modify_section`
  needed for this half — frontmatter writes are not gated by
  `allowed_callers` (that only applies to body sections).
- `resolve_opportunity()`/`_iter_opportunity_notes()` (title/`--customer`
  matching, ambiguity handling) stay entirely hand-written, untouched —
  real, Opportunity-specific business logic, not mechanics.
- The `## Related` section write, its local `_CALLER_ALLOW_LISTS` guard,
  and the local `insert_body_section_if_missing`/`read_body_section`/
  `replace_body_section` primitives are UNTOUCHED by this task — `T02`'s
  own scope.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/track-opportunities/scripts/link_opportunity.py`
- `Hermes-Provisioning/skills/company-review/track-opportunities/scripts/vault_manager.py` (resync only if the freshness check finds real drift from the canonical source — not expected)

---

## Constraints

- Inherits from parent story.
- `resolve_opportunity()`/`_iter_opportunity_notes()` stay exactly as-is,
  hand-written.
- The "never fabricate a Customer/Opportunity" discipline holds exactly
  as today — an unresolvable target is always a real error, never a
  created stand-in.
- No new `vault_manager.py` copy is deployed — reuse the already-current
  copy; resync in place only if drift is genuinely found.
- Verify against a scratch vault, distinct `--vault-path`.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`, real
`thread`/`meeting` Template.json files and a real Opportunity-note shape
copied from the real, live vault):**

1. (Unlabeled, supporting) Diff `track-opportunities/scripts/
   vault_manager.py` against `Hermes-Provisioning/shared/vault_manager.py`
   directly; confirm byte-identical (or resync and re-confirm if not).
2. `[REQ-SB-88-US-02-AC-01]` Given a scratch Thread or Meeting note not yet
   linked to a real scratch Opportunity, run the migrated
   `link_opportunity.py`; confirm the note's own `opportunities`
   frontmatter list gains a `[[<Opportunity title>]]` wikilink, and the
   script still prints `{linked, note_path, opportunity_path}` with the
   same meaning as today.
3. `[REQ-SB-88-US-02-AC-03]` Given more than one scratch Opportunity note
   sharing the same title under different Customers, run
   `link_opportunity.py` without `--customer`; confirm it reports the real
   candidate paths and refuses to guess. Re-run with the correct
   `--customer`; confirm it resolves to the single intended Opportunity
   and links it.
4. `[REQ-SB-88-US-02-AC-04]` Given no real Opportunity note matches the
   given title (with or without `--customer`), run `link_opportunity.py`;
   confirm it returns a real `{"error": ...}`, creates nothing, links
   nothing.

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Deployed `vault_manager.py` freshness reconfirmed (diff or resync +
      re-diff)
- [x] `opportunities` frontmatter-list write migrated onto
      `vm.read_note`/`vm.update`
- [x] `resolve_opportunity()`/`_iter_opportunity_notes()` byte-for-byte
      unchanged
- [x] Ambiguous-title resolution and no-match refusal both unaffected
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `## Related` section write, per-caller access-guard question — `T02`.
- Real-vault retrofit verification — `T03`.

---

## Context / Notes

`architecture.md` → `§track-opportunities Link-Write Migration
(REQ-SB-88-US-02)` and `ADR-017` are authoritative. Read the real current
`link_opportunity.py` directly before editing (reproduced in Starting
State above from this session's own read).

---

## Implementation Log

**2026-09-02, coder.** Diffed `track-opportunities/scripts/
vault_manager.py` against the canonical `Hermes-Provisioning/shared/
vault_manager.py` directly (`diff` byte comparison) — confirmed
byte-identical, no resync needed. Migrated `link_opportunity()`'s
`opportunities` frontmatter-list write onto `vm.read_note(note_path)` +
`vm.update(vault_path, note_path, frontmatter={"opportunities":
merged_list})`, replacing the local hand-rolled frontmatter-line splice
(same shape `apply_thread_review.py`'s own frontmatter stamping already
uses). `resolve_opportunity()`/`_iter_opportunity_notes()` untouched,
still using the local `read_note` (real, Opportunity-specific business
logic, unaffected). `## Related` write, `_RELATED_CALLER`/
`_CALLER_ALLOW_LISTS` guard, and the local `insert_body_section_
if_missing`/`read_body_section`/`replace_body_section` primitives are
UNTOUCHED by this task (still functioned correctly end-to-end as a side
effect of running the real script, confirmed below) — `T02`'s own scope.

**Verification (scratch vault at `<scratchpad>/sb85-us02-vault`,
`.second-brain/data/Templates/thread`+`meeting` Template.json copied
byte-identical from the real, live vault; a scratch Thread B and a
scratch Meeting B, both with empty `opportunities: []`; two scratch
Opportunity notes both titled "Renewal 2026", one under
`Work/Customers/Acme Corp/Opportunities/`, one under
`Work/Customers/Beta Corp/Opportunities/`):**

- (Unlabeled, supporting) **PASS.** `diff` confirmed
  `track-opportunities/scripts/vault_manager.py` byte-identical to
  `Hermes-Provisioning/shared/vault_manager.py`.
- `[REQ-SB-88-US-02-AC-01]` **PASS.** Ran the migrated
  `link_opportunity.py` against scratch Thread B with `--customer
  "Acme Corp"` (after first confirming ambiguity below): output
  `{"linked": true, "note_path": ..., "opportunity_path": ...}` — same
  meaning as today. Confirmed on disk: Thread B's `opportunities`
  frontmatter list gained `["[[Renewal 2026]]"]` via the migrated
  `vm.update` call.
- `[REQ-SB-88-US-02-AC-03]` **PASS.** Ran `link_opportunity.py` against
  Thread B for `"Renewal 2026"` WITHOUT `--customer`: `{"error":
  "'Renewal 2026' matches more than one Opportunity -- pass --customer
  to disambiguate", "candidates": [<Acme path>, <Beta path>]}` — refused
  to guess, real candidate paths reported. Re-ran WITH `--customer
  "Acme Corp"`: resolved to the single Acme Opportunity and linked it
  (see AC-01 above).
- `[REQ-SB-88-US-02-AC-04]` **PASS.** Ran `link_opportunity.py` against
  Thread B for `"Nonexistent Opp"` (no real match, with or without
  `--customer`): `{"error": "no Opportunity named 'Nonexistent Opp'
  exists -- create it first"}`, exit code `1`. Confirmed no note was
  created anywhere under `Work/Customers/` for this title.

**Assumptions (scope-internal, for human spot-check):** none beyond
ordinary scratch-fixture construction (two same-titled Opportunities
under different Customers, matching the story's own AC-03 scenario
exactly).

gate: clear 2026-09-02 — no MUST-FLAG trigger fired (freshness
reconfirmed with a real positive result, all four locked ACs touched by
this task verified live, no new dependency/interface change, no ADR
touched).
