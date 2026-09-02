---
id: REQ-SB-87-US-04-T03
title: Converge apply_thread_review.py onto the Thread template's own section-access declarations
parent_story: REQ-SB-87-US-04
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-04-T02]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-04-T03 — Converge apply_thread_review.py Onto the Thread Template's Own Section-Access Declarations

## Parent Story

- Story: [[REQ-SB-87-US-04]] — `../UserStories/REQ-SB-87-US-04-summarize-and-tag-threads-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Retire `apply_thread_review.py`'s own separate `_HUMAN_OWNED_HEADERS`/
`_CALLER`/`replace_body_section` access-control constants and function,
relying exclusively on `vault_manager.py`'s template-declared per-caller
access for every section write this script performs.

---

## Starting State → End State

**Before / Inputs:**
- `apply_thread_review.py`'s own real, separate guard (read directly,
  2026-09-01): `_HUMAN_OWNED_HEADERS = frozenset({"## Personal Notes", "##
  Actions"})`, `_CALLER = "apply_thread_review.apply_thread_review"`,
  enforced inside its own local `replace_body_section()` — `if header in
  _HUMAN_OWNED_HEADERS or caller != _CALLER: raise PermissionError(...)`.
  This local guard is now fully superseded by `T01`'s migration onto
  `vault_manager.modify_section`, which already enforces access via the
  Thread template's own declarations (`REQ-SB-87-US-01-T05`).

**After / Outputs:**
- The local `_HUMAN_OWNED_HEADERS`/`_CALLER`/`replace_body_section`/
  `insert_body_section_if_missing` functions and constants are removed
  from `apply_thread_review.py` — every section write already goes
  through `vault_manager.modify_section` (`T01`), which enforces access
  purely from the Thread template's own `allowed_callers` declarations.
- `## Summary` write succeeds (caller `apply_thread_review` is on its
  `allowed_callers` list); any attempt to write `## Personal Notes`
  through this code path is refused with a real, explicit
  `VaultManagerError` — enforced by `vault_manager.py`'s own
  template-declared access control, never by any code local to this
  script anymore.
- `read_note`/`merge_tags`/`upsert_frontmatter_key`'s own now-dead local
  copies (superseded by `T01`/`T02`'s migration onto the shared engine)
  are also removed if no longer called by anything in this file — a real,
  disclosed dead-code cleanup, not a behavior change.

---

## Files to Modify

- `Hermes-Provisioning/skills/company-review/summarize-and-tag-threads/scripts/apply_thread_review.py`

---

## Constraints

- Inherits from parent story.
- Zero behavior change to any already-working write path — this task only
  removes the now-redundant local guard/primitives, it does not change
  WHAT gets written or WHO may write it (the Thread template's own
  declarations already reproduce the exact same real restrictions).
- Verify against a scratch vault, distinct `--vault-path`.

---

## Tests

**Manual verification steps (scratch vault, distinct `--vault-path`):**
1. `[REQ-SB-87-US-04-AC-06]` Confirm `## Summary` is still written
   successfully through the migrated code path (caller
   `apply_thread_review`, on the Thread template's own `allowed_callers`
   for that section).
2. `[REQ-SB-87-US-04-AC-06]` Attempt (via a disposable throwaway script,
   not this Skill's own real entry point) a `## Personal Notes` write
   through the migrated code path; confirm it is refused with a real,
   explicit `VaultManagerError`, and confirm — by reading the finished
   `apply_thread_review.py` directly — that this refusal is enforced by
   `vault_manager.py`'s own template-declared access control, not by any
   `_HUMAN_OWNED_HEADERS`-shaped constant still present in this file.
3. (Unlabeled, supporting) Confirm `_HUMAN_OWNED_HEADERS`/`_CALLER`/the
   local `replace_body_section`/`insert_body_section_if_missing` are no
   longer present in the file (or, if any function name is kept for a
   real, disclosed reason, confirm it is no longer load-bearing for access
   control).

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via scratch-vault CLI runs`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `_HUMAN_OWNED_HEADERS`/local `_CALLER`-based guard removed
- [x] `## Summary` write succeeds; `## Personal Notes` write refused, both
      enforced solely by `vault_manager.py`'s template-declared access
- [x] Zero behavior change to any already-working write path
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint (n/a — no new hard rule, see Implementation Log)
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `REQ-SB-87-US-05`'s own new `## Actions` write — this task only proves
  `## Summary`/`## Personal Notes` per its own locked Scenario 6; `##
  Actions` access is enabled by this same template but not exercised
  until `REQ-SB-87-US-05` actually writes to it.
- Real-vault verification / cutover — `T04`.

---

## Context / Notes

Read the real current `apply_thread_review.py` directly before editing
(reproduced in Starting State above from a 2026-09-01 read).

---

## Implementation Log

**2026-09-01, coder.**

**Real current-state read confirmed before editing:** re-read
`apply_thread_review.py` directly (2026-09-01) — `_HUMAN_OWNED_HEADERS`/
`_CALLER`, `insert_body_section_if_missing`, `replace_body_section` were
all still present but had ZERO remaining callers anywhere in the file
(`## Summary`'s write already fully migrated onto `vm.modify_section` at
`T01`; tag-merge onto `vm.merge_tags` at `T02`). `upsert_frontmatter_key`
also had zero remaining callers (superseded by `vm.update` at `T01`).
`read_note` stays — still genuinely used by `build_company_index` and the
latest-message-date lookup.

**Reconciled the launcher's own parenthetical against `ADR-017` directly,
per instruction — read both, didn't assume:** `ADR-017`'s own Decision
section states `## Actions` → `allowed_callers: ["apply_thread_review"]`
— "the SAME identity as `## Summary` — one caller, two sections", not a
different future caller. Confirmed directly against the real, live
vault's own `Templates/thread/Template.json`
(`C:/myWorx/Moussa MD/Moussa Brain/.second-brain/data/Templates/thread/
Template.json`) — matches `ADR-017` exactly. This task's own locked scope
(Scenario 6 / `AC-06`) only exercises `## Summary`/`## Personal Notes`;
`## Actions` access is enabled by the same template declaration but not
exercised by this script until `REQ-SB-87-US-05` actually adds an
Actions-write call — per this task's own Out of Scope, unaffected by the
caller-identity clarification either way.

**What was changed (`apply_thread_review.py` only, per `## Files to
Modify`):**
- Removed `_HUMAN_OWNED_HEADERS`, `_CALLER`, `insert_body_section_if_missing`,
  `replace_body_section` — the file's own separate, now fully superseded
  access-control guard and hand-rolled section writers.
- Removed `upsert_frontmatter_key` (superseded by `vm.update` at `T01`) and
  its now-orphaned helpers `_format_frontmatter_value` and
  `_BODY_SECTION_HEADER_PATTERN` (each had zero remaining callers once
  `upsert_frontmatter_key` was gone) — logged here as the same kind of
  scope-internal dead-code cleanup `T02` already established for the local
  `merge_tags` removal, not scope creep.
- `read_note`, `_parse_frontmatter_value`, `_FRONTMATTER_LINE`,
  `_LIST_ITEM_PATTERN` kept — still genuinely called.
- Updated the module docstring: corrected the stale "stay defined ...
  retired only at T03" forward-looking note (now reads as history) and
  added a new dated paragraph documenting this convergence.
- Company resolution, the never-tag-Person-notes rule, `append_log_entry`,
  and every already-migrated `T01`/`T02` call site are byte-for-byte
  unchanged — confirmed by diff-review of the final file against the
  pre-edit read.

**Live verification (fresh scratch vault, distinct `--vault-path`, built
at a session-scoped scratchpad directory — real `thread` Template.json
copied byte-identical from the real, live vault's own `.second-brain/
data/Templates/thread/Template.json`; synthetic Customer/Partner/Person/
Thread/RawMessage content, same shapes T01/T02 already used):**

- `[REQ-SB-87-US-04-AC-06]` **PASS, both halves.**
  - Positive half: ran the real, migrated `apply_thread_review.py` CLI
    against a real scratch Thread with no pre-existing `id` — `## Summary`
    written successfully (`"Kickoff call about renewing Acme's annual
    contract."`), `id` minted and persisted, exactly matching `T01`'s own
    already-verified shape. Re-confirmed by reading the finished note on
    disk.
  - Negative half: a disposable throwaway script (not this Skill's own
    real entry point — a standalone script that imports the real,
    unmodified `vault_manager.py` directly) attempted
    `vm.modify_section(..., section="Personal Notes", caller=
    "apply_thread_review")` against that same real Thread note. Refused
    with a real `VaultManagerError`: `"section 'Personal Notes' is
    'human_only' in template 'thread' -- no automated write is allowed
    here"`. Confirmed the target file was byte-identical before/after the
    refused attempt (`before_text == after_text` → `True`). This refusal
    comes from `vault_manager.py`'s own `_require_machine_write`/
    `_section_access` reading the Thread template's own `"access":
    "human_only"` declaration — `apply_thread_review.py` itself no longer
    defines any `_HUMAN_OWNED_HEADERS`-shaped constant at all (confirmed
    by grepping the finished file: the only remaining matches are prose
    inside the module docstring's own migration-history paragraphs, zero
    live code).
- **(Unlabeled, supporting)** Confirmed via direct grep of the finished
  file: `_HUMAN_OWNED_HEADERS`, `_CALLER`, `insert_body_section_if_missing`,
  `replace_body_section`, `upsert_frontmatter_key`, `_format_frontmatter_value`,
  `_BODY_SECTION_HEADER_PATTERN` are ALL absent as live code — every
  remaining textual match is inside the docstring's own historical prose.
  `python -m py_compile` on the modified file — clean.
- **Full regression re-run of `T01`/`T02`'s own scenarios (zero-regression
  check, per this task's mandate)** — ran the real, migrated
  `apply_thread_review.py` against 3 scratch Threads (A → B → C, mirroring
  `T02`'s own A/B/C shape: a resolvable + unresolvable company case, a
  no-pre-existing-tags case with a Customer+Partner pair, and an
  out-of-order-arrival log-entry case), plus a re-run of A for an
  idempotence check:
  - `[REQ-SB-87-US-04-AC-01]` **PASS.** `## Summary` written on every run
    with the real agent-provided content; every resolved company's
    `customer/<slug>`/`partner/<slug>` tag merged onto the Thread AND every
    message under it (confirmed on disk); output JSON contract unchanged
    (`{tags_applied, companies_unresolved, messages_tagged,
    log_entries_added, last_message_at, last_summarized_at}`).
  - `[REQ-SB-87-US-04-AC-02]` **PASS.** `last_message_at`/
    `last_summarized_at` correctly stamped on every run (confirmed on
    disk against each Thread's own real message `received` value).
  - `[REQ-SB-87-US-04-AC-03]` **PASS.** `Acme-log.md` read back correctly
    newest-to-oldest across all 3 entries, including the out-of-order
    08-15 entry (added last, in run C) landing in the correct MIDDLE
    position, not appended at the end; `BetaPartner-log.md` correctly got
    its own single entry from run B; re-running Thread A a second time
    produced zero duplicate log line.
  - `[REQ-SB-87-US-04-AC-04]` **PASS.** Both real Person notes (`Jane
    Doe`, `Sam Internal`, each linked via `participant_links` from a
    tagged Thread/message) read back byte-identical to their pre-run
    state after all 4 runs — zero tag changes to either.
  - `[REQ-SB-87-US-04-AC-05]` **PASS.** `"Ghost Company Not Real"`
    reported in `companies_unresolved`; confirmed no `Ghost*` folder/note
    exists anywhere under `Work/Customers` or `Work/Partners` after the
    full run sequence.
- `git status` confirms only `apply_thread_review.py` (this task's one
  `## Files to Modify` entry) was touched under this Skill's `scripts/`
  folder — `vault_manager.py` remains untracked from `T01`'s own
  deployment, not touched by this task.

**MEMORY.md:** not updated — no new decision/pattern/constraint. The
governing architectural decision (per-caller section access declared in
`Template.json`, retiring hardcoded Python guards) was already recorded
at `ADR-017` and MEMORY.md's own 2026-08-25 `vault_manager.py` entry; this
task only executes the already-decided retirement, same judgment `T02`
already made for its own dead-code removal.

**Out of scope, not silently absorbed (per this task's own Out of
Scope):** `## Actions` write access is enabled by the same template
declaration this task relies on, but is not exercised by this script
until `REQ-SB-87-US-05` actually adds that write call. Real-vault
verification / `job4` cutover stays `T04`'s own scope.

gate: clear 2026-09-01 — no MUST-FLAG trigger fired: no new dependency, no
shared-interface change beyond what `T01`/`T02`/`ADR-017` already named, no
ADR touched by this task itself, no contradictory input (the launcher's
own `## Actions`-caller parenthetical was reconciled directly against
`ADR-017`, not guessed at), all locked verification points (`AC-06` both
halves, plus a full `AC-01`-`AC-05` regression re-run) passed live. The
dead-code-removal judgment call above (`upsert_frontmatter_key`'s orphaned
helpers) is logged for human spot-check per hard rule 5, not a flag
trigger.
