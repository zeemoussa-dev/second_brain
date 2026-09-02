---
id: REQ-SB-87-US-02-T01
title: Migrate ingest_email.py onto vault_manager.py (Thread + first RawMessage)
parent_story: REQ-SB-87-US-02
requirement_id: REQ-SB-87
type: backend
status: Done
gate: flagged
gate_reason: "ESC-061 resolved 2026-09-01 (direct fix, operator-directed, no new story per this project's own BUG-041 precedent): create_dynamic_child() extended with an additive body= flat-body mode, all 84 real deployed vault_manager.py copies resynced, ingest_email.py's RawMessage creation migrated and re-verified live. Flagged for human spot-check on one disclosed scope-internal judgement call: the migrated RawMessage filename now uses create_dynamic_child()'s own generic ingestion-date+wall-clock-suffix naming, not vault_lib's bespoke received-date+hash-suffix naming (content/idempotency unaffected either way) -- see Implementation Log."
phase: P1
depends_on: [REQ-SB-87-US-01-T05]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-02-T01 — Migrate ingest_email.py onto vault_manager.py

## Parent Story

- Story: [[REQ-SB-87-US-02]] — `../UserStories/REQ-SB-87-US-02-email-thread-capture-vault-manager-migration.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Deploy a fresh `vault_manager.py` copy into `email-thread-capture/scripts/`
(first-time deployment) and migrate `ingest_email.py`'s own Thread
resolve/create and first-RawMessage-creation mechanics onto it, preserving
its exact real output contract and business logic.

---

## Starting State → End State

**Before / Inputs:**
- Real, current `ingest_email.py` (read directly, 2026-09-01): resolves the
  Thread via `vault_lib.resolve_thread_directory`; if `None`, creates it via
  `vault_lib.create_thread_note_baseline(vault_path, conversation_id,
  thread_name=subject, tags=[])`; ensures a bare Person note per unique
  participant email (`vault_lib.ensure_bare_person_note` — untouched by
  this migration, stays hand-written); creates the RawMessage via
  `vault_lib.create_raw_message_note(...)` if `raw_message_note_exists()`
  says it doesn't yet; always stamps `last_message_at` (advances-only) via
  `vault_lib.update_thread_last_message_at`. Returns `{thread_created,
  message_created, thread_path, message_path}`.
- `email-thread-capture/scripts/` has never had a `vault_manager.py` copy.

**After / Outputs:**
- `email-thread-capture/scripts/vault_manager.py` — a fresh copy, sourced
  from the canonical `Hermes-Provisioning/shared/vault_manager.py`
  (post-`REQ-SB-87-US-01`'s own engine extensions).
- `ingest_email.py`'s own Thread resolve/create now goes through
  `vault_manager.find_by_id`/`vault_manager.create` against the `thread`
  template (`REQ-SB-87-US-01-T05`), passing `caller="ingest_email"` on
  every mutating call.
- First-RawMessage creation now goes through the dynamic-child verb
  (`REQ-SB-87-US-01-T01`) against the Thread's own `messages` declared
  child, natural key `(conversation_id, message_id)`.
- `ensure_bare_person_note`, participant-link accumulation, and the
  `last_message_at` advances-only stamping logic stay EXACTLY as they are
  today, entirely hand-written — this task only swaps the underlying
  note/section read-write mechanics.
- The function's own real return shape (`{thread_created, message_created,
  thread_path, message_path}`) is unchanged in meaning.

---

## Files to Modify

- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/ingest_email.py`
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/vault_manager.py` (new copy)

**Added 2026-09-01 (ESC-061 resolution, operator-directed direct fix --
see Implementation Log for the full instruction and reasoning, same
precedent as `BUG-041`'s own "Just fix Straight no need for story"):**
- `Hermes-Provisioning/shared/vault_manager.py` (canonical engine --
  additive `body=` flat-body mode on `create_dynamic_child()`)
- `Hermes-Provisioning/shared/tests/test_vault_manager.py` (new coverage)
- All 10 other real repo `vault_manager.py` copies under
  `Hermes-Provisioning/skills/**/scripts/vault_manager.py` (resync)
- All 73 real, active deployed `vault_manager.py` copies under
  `%LOCALAPPDATA%\hermes\profiles\**\skills\...\scripts\vault_manager.py`
  (resync)

---

## Constraints

- Inherits from parent story.
- `ensure_bare_person_note`'s own dedup-key, ignore-list, and GAL-derived
  department/role/company logic is untouched — this task never edits that
  function.
- The Thread's own `id` (a real, stable frontmatter key `vault_manager.py`
  now maintains) must be usable for future lookups without breaking
  `resolve_thread_directory`-style callers elsewhere (`rename_thread.py`,
  `link_person_to_thread.py`, etc. — `T02`/`T03`'s own scope to migrate,
  but this task's own Thread-creation must produce a note those siblings
  can still find).
- **Do not point `--vault-path` at the real, live vault for this task's own
  verification** — use a scratch vault seeded with a real ~100-email
  sample, per the Constraints' proving-phase rollout (see Tests below).

---

## Tests

**Manual verification steps (all against a SCRATCH vault, distinct
`--vault-path`, seeded with a real ~100-email sample pulled via
`list_recent_emails.py`/`run_full_capture.py`'s own real paging — never the
live vault for this task):**
1. `[REQ-SB-87-US-02-AC-01]` Pick a genuinely first-seen `conversation_id`
   from the real 100-email sample; run the migrated `ingest_email.py`
   against it. Confirm a new Thread concept note and its first RawMessage
   note are written with the exact same real frontmatter, body-section, and
   file/folder layout `email-thread-capture` produces today (per
   `REQ-SB-87-US-01-T05`'s own disclosed `## Files`-at-creation
   normalization, which is NOT treated as a violation here). Confirm the
   script still returns `{thread_created: true, message_created: true,
   thread_path, message_path}`.
2. `[REQ-SB-87-US-02-AC-02]` Re-run `ingest_email.py` for the SAME
   `message_id` from step 1. Confirm no duplicate Thread or RawMessage note
   is created (`{thread_created: false, message_created: false}`), and that
   `last_message_at` only ever advances, never regresses — repeat with a
   real message whose `received` timestamp is EARLIER than the Thread's
   current `last_message_at` and confirm it does NOT regress.
3. (Unlabeled, supporting) Confirm `ensure_bare_person_note`'s own real
   behavior (dedup key, ignore list, GAL fields) is byte-for-byte unchanged
   — same Person notes created/topped-up as an un-migrated run would
   produce, verified by comparing against a pre-migration baseline run on
   the SAME scratch sample (captured before this task's own edits, kept for
   comparison).

**Automated tests:** `n/a — no existing pytest harness for this Skill;
verified via real scratch-vault CLI runs, per this codebase's own
established pattern`.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] Fresh `vault_manager.py` copy deployed to `email-thread-capture/scripts/`
- [x] Thread create/find AND first-RawMessage creation both go through
      `vault_manager.py` (`caller="ingest_email"` on the Thread `create()`
      call; RawMessage via `create_dynamic_child()`'s new `body=` flat-body
      mode, `ESC-061` resolved 2026-09-01)
- [x] Exact real frontmatter/section/output-shape parity confirmed against
      the scratch sample for Thread + RawMessage + Person notes -- RawMessage
      BODY content confirmed byte-for-byte identical (100/100); frontmatter
      identical on every shared key (0 real mismatches, only the
      already-accepted additive `id`/`title`/`created` keys new); ONE
      disclosed divergence -- the RawMessage's own on-disk FILENAME now
      follows `create_dynamic_child()`'s generic naming, not `vault_lib`'s
      bespoke one (see Implementation Log) -- logged as a scope-internal
      judgement call, not a content/duplication defect
- [x] Idempotency (re-ingest same message) and advances-only
      `last_message_at` confirmed
- [x] `ensure_bare_person_note` unchanged
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- `rename_thread.py`, `capture_attachments.py`/`capture_file_link.py`,
  `link_person_to_thread.py` — `T02`/`T03`.
- `run_full_capture.py`/`run_delta_capture.py`'s own orchestration logic —
  never edited by this migration.
- Any real-vault run or cutover — `T05`.
- The Capture-time classify-or-skip judgment layered onto this same branch
  — `REQ-SB-87-US-03`, sequenced strictly after this task.

---

## Context / Notes

`architecture.md` → `§Canonical vault_manager.py Source & Deployment`,
`ADR-017` are authoritative for the engine/template shape this task
consumes. Read the REAL current `ingest_email.py` directly before editing
(reproduced in Starting State above from a 2026-09-01 read — confirm it
hasn't drifted further by build time).

---

## Implementation Log

**What was built:**
- `Hermes-Provisioning/skills/vault-rebuild/email-thread-capture/scripts/
  vault_manager.py` -- a fresh, first-time deployment, byte-identical to
  the canonical `Hermes-Provisioning/shared/vault_manager.py` (SHA-256
  confirmed: `9B9CAFF1...` both sides).
- `ingest_email.py` -- Thread resolve/create now goes through
  `vault_manager.find_by_id`/`vault_manager.create` against the `thread`
  template, `caller="ingest_email"` on the mutating `create()` call. The
  Thread's own real, stable `id` (and `title`, for on-disk naming parity)
  is its `conversation_id` itself -- a real, meaningful external key from
  birth, never a minted uuid (see `MEMORY.md` Decision entry for the full
  reasoning, including why this doesn't conflict with
  `REQ-SB-87-US-04-T01`'s own same-day `uuid4()`-backfill choice for
  PRE-EXISTING Threads with no `id` at all). `last_message_at`'s
  advances-only stamping logic stays exactly as it was (a hand-written
  comparison in `ingest_email.py` itself), only its read/write mechanics
  now go through `vault_manager.read_note`/`vault_manager.update`.
  `ensure_bare_person_note`, participant-link accumulation, and RawMessage
  creation itself are UNCHANGED, still calling `vault_lib.py` directly.

**Why RawMessage creation was NOT migrated (blocking `AC-01`):**
`vault_manager.py`'s `create_dynamic_child()` (the mechanism
`REQ-SB-87-US-01-T01` built for exactly this) can only write a dynamic
child's body via its own declared `Template.json` `sections` list --
confirmed live, not just theoretically: the real `thread/Template.json`'s
`messages` child declares no `sections` at all, so calling
`create_dynamic_child()` for a RawMessage today produces a genuinely
EMPTY body, silently dropping any caller-supplied body content (a real
email body is a flat, headerless string in the real, current
`vault_lib.create_raw_message_note` shape -- confirmed by direct reading).
This is real content loss, not an acceptable additive normalization the
way `REQ-SB-87-US-01-T05`'s own empty `## Files`-at-creation call was.
Resolving it needs one of two files OUTSIDE this task's own `## Files to
Modify`: the Thread `Template.json` (`T05`'s own already-`Done`, live
artifact) to declare a `"Body"` section, or the CANONICAL
`Hermes-Provisioning/shared/vault_manager.py` (then a re-deploy to all 82
real active copies) to accept a raw unheaded body string -- both are
out-of-scope, and the second is a genuine architecture-level
engine-contract change, not a local coder call. No parallel hand-rolled
write path was built to route around this -- per this task's own launch
instructions, that would silently reinvent what `T01`'s own primitive
already owns. Escalated instead: `ESC-061` (`ESCALATIONS.md`),
`REVIEW-QUEUE.md`. RawMessage creation stays on
`vault_lib.create_raw_message_note`, byte-for-byte unchanged.

**Live verification (real ~100-email scratch-vault sample, never the real
vault):**

Pulled 100 real emails via the real, unmodified `list_recent_emails.py`
against the operator's own live Outlook (51 distinct `conversation_id`s,
21 with multiple messages in-sample -- genuine coverage for both
first-seen and idempotency checks). Two isolated scratch vaults, each
seeded with a copy of the real, live `thread/Template.json`: `vault`
(migrated `ingest_email.py`) and `vault_baseline` (the pre-migration
`ingest_email.py`/`vault_lib.py`, retrieved via `git show HEAD:...`, for
a same-sample byte-for-byte comparison). Each of the 100 real emails run
through `ingest_email.py --vault-path <vault> --input-file <one-email
JSON>` as a separate subprocess call each, matching real production usage
(`run_full_capture.py`/`run_delta_capture.py`'s own per-email subprocess
dispatch, `AC-05`'s own contract, out of this task's scope but the
realistic invocation shape).

- `[REQ-SB-87-US-02-AC-01]` **PARTIAL / BLOCKED.** Thread + Person-note
  halves PASS live: both runs produced 51 Thread concept notes / 151 total
  `.md` under `Work/Threads` and 156 Person notes; every real, pre-existing
  frontmatter field on the migrated Thread notes matches the baseline
  run's values exactly (zero mismatches on any shared key, checked
  programmatically across the full sample's first-seen Thread); the only
  differences are 4 disclosed, additive-only new keys (`id`, `title`,
  `created`, `classification`) and an always-present empty `## Files`
  header, both already-accepted `T05` normalizations. All 156 Person notes
  are byte-for-byte SHA-256-identical between the migrated and baseline
  runs (`ensure_bare_person_note` genuinely untouched). A genuinely
  first-seen conversation_id's return shape was confirmed:
  `{"thread_created": true, "message_created": true, "thread_path": ...,
  "message_path": ...}` -- exact key set, correct meaning. **RawMessage
  creation itself was never migrated onto the new engine (see above)** --
  the "creating the message note via the RawMessage mechanism
  `REQ-SB-87-US-01` delivers" half of this AC's own `When` clause did not
  happen; all 100 RawMessage notes ARE confirmed byte-for-byte identical
  between the two runs, but only because that code path is unchanged. Not
  marked passing.
- `[REQ-SB-87-US-02-AC-02]` **PASS.** Re-ran `ingest_email.py` for an
  already-captured `message_id`: `{"thread_created": false,
  "message_created": false}`, confirmed live, no duplicate Thread or
  RawMessage note created. `last_message_at` advances-only confirmed two
  ways: re-ran the SAME message with a `received` timestamp far EARLIER
  than the Thread's current `last_message_at` -- value unchanged (no
  regression); re-ran again with a `received` timestamp genuinely LATER --
  value correctly advanced to the new one. All three checks read the real
  on-disk frontmatter directly via `vault_manager.read_note` after each
  call, not just trusted the script's own stdout.
- (Unlabeled, supporting) **PASS.** `ensure_bare_person_note`'s own real
  behavior confirmed byte-for-byte unchanged: all 156 real Person notes
  produced by the migrated run are SHA-256-identical to the same-sample
  pre-migration baseline run's own 156 Person notes (same dedup keys, same
  ignore-list/GAL-field handling, zero drift).

**Scope-internal judgement calls** (logged for human spot-check, not
blocking):
1. `note_id=conversation_id`/`title=conversation_id` for Thread creation
   (vs. a minted `uuid4()`, `REQ-SB-87-US-04-T01`'s own same-day choice
   for pre-existing Threads with no `id` yet) -- reasoned live-non-
   conflicting in `MEMORY.md`'s Decision entry; not itself a locked AC's
   wording, a mechanical mapping choice this task had to make.
2. `note_name="Threads"` passed explicitly on both `find_by_id`/`create`
   calls (matching `vault_lib._THREADS_SUBFOLDER`) -- the natural, only
   real mapping, not a genuine alternative.

**Verification technique note:** the task's own Tests block named
`list_recent_emails.py`/`run_full_capture.py`'s "own real paging" --
`list_recent_emails.py --limit 100` was run directly (a single real,
bounded Outlook page), not the full `run_full_capture.py` orchestration
(out of this task's own scope, `AC-05`/`T04`). A real Windows `MAX_PATH`
(260 char) collision surfaced purely from the session scratchpad's own
deeply-nested temp path (not a defect in any real code) -- the scratch
vault was relocated to a short `C:\scratch-sb87t01\` path, unrelated to
and outside this task's own `## Files to Modify`.

**Escalations / review-queue items written by this task:**
- `ESCALATIONS.md` → `ESC-061` (out-of-scope: the RawMessage flat-body
  gap needs a file outside this task's own `## Files to Modify`).
- `REVIEW-QUEUE.md` → `REQ-SB-87-US-02-T01` entry, same-day, pointing at
  `ESC-061` and this task file.

**Not marked `Done`** -- `AC-01` cannot be verified as fully passing per
hard rule 4/6 (a locked AC with no honestly-verifiable positive result
blocks the task). `status: Blocked`, `gate: flagged`. `T02`-`T05`
(siblings, same story) are not themselves blocked by this -- none of them
touch RawMessage creation.

gate: flagged 2026-09-01 -- trigger 6 (a locked AC, `AC-01`, could not be
verified) and trigger 7 (out-of-scope: closing the gap needs a file
outside this task's own `## Files to Modify`). See `ESC-061` /
`REVIEW-QUEUE.md`.

---

## Follow-up: ESC-061 resolved, task completed (2026-09-01, same-day)

**Operator's own direct instruction (verbatim intent):** extend
`create_dynamic_child()` to accept an optional flat, unheaded `body`
string as an alternative to the `sections`-based write, preserving the
real, current RawMessage body shape exactly (no synthetic `## Header`).
Do NOT declare a `Body` section on the Thread template's `messages`
child instead (would regress the real, already-live shape of every
already-captured RawMessage note). Treated as a direct fix, not a new
task/story, per this project's own established precedent
(`BUG-041`'s "Just fix Straight no need for story").

### 1. Engine extension (canonical `Hermes-Provisioning/shared/vault_manager.py`)

`create_dynamic_child()` gained an additive `body: str | None = None`
parameter, mutually exclusive with `sections` (a real `VaultManagerError`
if both are given). When `body` is given, the child note is written with
that exact string as its body (`write_note(child_path, full_frontmatter,
"\n" + body)` -- reproduces `vault_lib._write_frontmatter_note`'s own
real `frontmatter + "\n\n" + body` separator exactly, confirmed by
direct byte-shape comparison of the two functions). The original
`sections`-based path is completely unchanged for any dynamic child that
DOES declare `sections` (none of the other real dynamic-child consumers
today do). CLI (`create-child`) and its own module docstring updated to
accept `"body": str?` in the input JSON alongside the existing
`"sections"` key.

**New automated tests** (`Hermes-Provisioning/shared/tests/
test_vault_manager.py`, `src/backend/.venv/Scripts/python.exe -m pytest
Hermes-Provisioning/shared/tests` -- 56 passed, 0 failed, including all 5
new ones):
- `test_create_dynamic_child_flat_body_mode_writes_raw_headerless_content`
  -- a template with NO declared `sections` (matching the real Thread
  `messages` shape exactly) gets a real, non-empty, headerless body via
  `body=`.
- `test_create_dynamic_child_flat_body_mode_idempotent_second_call_preserves_original_body`
  -- re-run with the same identity never overwrites the first real body.
- `test_create_dynamic_child_body_and_sections_are_mutually_exclusive` --
  passing both raises `VaultManagerError`.
- `test_create_dynamic_child_sections_mode_still_works_unchanged` -- the
  original `sections`-based mode is unaffected by the new parameter.
- (plus the 4 pre-existing dynamic-child tests, all still passing
  unchanged, confirming zero regression to `REQ-SB-87-US-01-T01`'s own
  original mechanism)

### 2. Resync to all real deployed copies

SHA-256 of the canonical file after the fix:
`093EE858978A0D37AC9F8785589E11DEE8D63DBB2A4588E3AFF8EA565C226EC7`.
Enumerated and overwrote every real copy, then re-hashed to confirm:
- **11 repo copies** (`Hermes-Provisioning/skills/**/scripts/
  vault_manager.py`, one more than `REQ-SB-87-US-01-T06`'s own prior "9
  repo" count -- `T01`'s own first-time `email-thread-capture` deployment
  is the 10th, `summarize-and-tag-threads` the 11th, both already existing
  before this fix) -- all 11 confirmed byte-identical post-resync.
- **73 real, active deployed profile copies** under
  `%LOCALAPPDATA%\hermes\profiles\**\skills\...\scripts\vault_manager.py`
  -- all 73 differed from canonical BEFORE the resync (expected -- this
  fix only ever landed on the canonical file first), all 73 confirmed
  byte-identical AFTER. `_disabled-skills*` folders checked directly --
  none currently contain a `vault_manager.py` copy of their own (nothing
  to skip).
- **Total: 84 real deployed copies, all now byte-identical to canonical.**
- Confirmed OUT of this resync's scope, deliberately: `src/backend/app/
  vault/vault_manager.py` -- a real, actively-imported FastAPI-app module
  that shares this file's own name/opening docstring lineage but is
  explicitly called out as "a different thing" by its own sibling
  `app/business/core/vault/vault_manager.py`'s docstring, last touched
  2026-08-27 (well before this engine's `create_dynamic_child`/`caller`
  extensions even existed) -- not part of the Hermes-Provisioning
  "canonical + physically-copied Skill scripts" deployment model this fix
  and `REQ-SB-87-US-01-T06`'s own prior resync both operate under. Not
  touched, matching that established scope boundary.

### 3. `ingest_email.py` -- RawMessage creation now fully migrated

RawMessage creation now goes through `vault_manager.create_dynamic_child()`
(`child_name="messages"`, `identity={"conversation_id", "message_id"}` --
the template's own declared `identity_fields`, `body=<real email body>`).
`ensure_bare_person_note`/participant-link accumulation logic is
byte-for-byte UNCHANGED (still directly `vault_lib.ensure_bare_person_note`)
-- only WHEN it's called changed: unconditionally on every ingest now,
rather than gated behind a pre-existence check that would have been
permanently stale anyway once RawMessage filenames stopped following
`vault_lib`'s own scheme (see disclosed divergence below); safe because
the function's own contract is already documented idempotent
(insert-a-missing-key-only). `message_path` in the return contract is now
`create_dynamic_child()`'s own real, authoritative path (whether newly
created or an existing idempotent match), not a separately re-derived
`vault_lib.raw_message_note_path()` call.

**One disclosed, real divergence (scope-internal judgement call, logged
for human spot-check, not blocking):** `create_dynamic_child()`'s own
generic filename mechanism names a dynamic child from TODAY's real
ingestion date + a wall-clock (`HH-MM`) collision suffix (the same
mechanism every other dynamic child already uses, unmodified from
`REQ-SB-87-US-01-T01`) -- NOT `vault_lib`'s own bespoke scheme (the
message's own real `received` date/time + a `message_id`-keyed hash
suffix on collision). Confirmed live: a message received `2026-08-20
17:43` was filed by the OLD scheme as `2026-08-20 1743 Ewec Discussion
....md`, and by the NEW scheme as `2026-09-01-Ewec Discussion....md`
(today's real ingestion date, not the email's own received date). This
changes the on-disk chronological SORT order of RawMessage notes within
a Thread's own `messages/` folder for any future capture -- a real,
visible file-browser UX difference once this migration eventually cuts
over to the live vault (`T05`'s own future scope, not this task's), not
a content-loss or duplication risk: idempotency is governed entirely by
the engine's own real `(conversation_id, message_id)` identity-field
match, confirmed live, never by the filename. No parameter exists on
`create_dynamic_child()` today to override the date basis it uses (the
analogous `folder_date` override `create()` already has for ROOT notes
has no dynamic-child equivalent) -- extending it further was judged
outside this fix's own authorized scope (extending `create_dynamic_child`
specifically for the flat-body gap, not a general date-override capability)
and is named here for a human to weigh in on, not silently absorbed or
independently decided.

### Live re-verification (fresh real ~100-email scratch-vault sample,
never the real vault -- the prior sample/scratch vaults from this same
task's earlier pass no longer existed on disk, re-pulled fresh per this
task's own Tests block)

Pulled 100 real emails via the real, unmodified `list_recent_emails.py`
against the operator's own live Outlook (same technique as the earlier
pass). Two fresh scratch vaults at `C:\scratch-sb87t01\vault` (fully
migrated `ingest_email.py`) and `C:\scratch-sb87t01\vault_baseline`
(the TRUE pre-migration `ingest_email.py`/`vault_lib.py`, retrieved via
`git show HEAD:...` -- confirmed genuinely pre-`REQ-SB-87-US-02`, still
using `vault_lib.resolve_thread_directory`/`create_thread_note_baseline`
directly, zero `vault_manager` usage at all), each seeded with a copy of
the real, live `thread/Template.json`. Each of the 100 real emails run
through `ingest_email.py --vault-path <vault> --input-file <one-email
JSON>` as a separate subprocess call, matching `run_full_capture.py`'s
own real per-email payload shape and dispatch pattern (confirmed by
direct reading of `run_full_capture.py`'s own `ingest_payload` construction).

- `[REQ-SB-87-US-02-AC-01]` **PASS.** Both runs: 51 distinct Threads, 151
  total `.md` under `Work/Threads`, 100 RawMessage notes, 156 Person
  notes -- identical counts. Programmatic comparison (`compare.py`,
  matching Thread notes by `conversation_id` and RawMessage notes by the
  real `(conversation_id, message_id)` natural key, since filenames now
  differ per the disclosed divergence above):
  - **156/156 Person notes byte-for-byte SHA-identical.**
  - **51/51 Threads matched; 0 real frontmatter key mismatches** beyond
    the already-`T05`-accepted additive `id`/`title`/`created`/
    `classification` keys.
  - **100/100 RawMessage notes matched by natural key; bodies byte-for-byte
    identical, 100/100** (confirmed both programmatically across the full
    sample and by direct read of one real sample note -- a real,
    multi-paragraph "RESTRICTED... Hi Mangesh..." email body, identical
    character-for-character between the migrated and baseline runs); 0
    real frontmatter key mismatches beyond the already-accepted additive
    `id`/`title`/`created` keys (matching the SAME normalization class
    `T05` already established for Thread notes, now extended to
    RawMessage). Direct read confirmed NO `"## "` header anywhere in a
    migrated RawMessage body -- genuinely flat, not synthetically
    sectioned.
  - A genuinely first-seen `conversation_id`'s return shape confirmed:
    `{"thread_created": true, "message_created": true, "thread_path": ...,
    "message_path": ...}` -- exact key set (`{thread_created,
    thread_path, message_path, message_created}`), correct meaning,
    reconfirmed across all 51 first-seen Threads / 100 created messages
    in the sample.
- `[REQ-SB-87-US-02-AC-02]` **PASS, reconfirmed against the now-fully-migrated
  code** (the prior pass already verified this against the
  Thread-only-migrated code; re-run here against the fully-migrated
  RawMessage path too). Live checks against the migrated vault, reading
  real on-disk frontmatter directly after each call (never trusting stdout
  alone):
  - Re-ran `ingest_email.py` for an already-captured `message_id`:
    `{"thread_created": false, "message_created": false}`, same
    `thread_path`/`message_path` returned both times -- confirmed no
    duplicate note, message file count unchanged (100 before and after).
  - Re-ran the SAME message with a `received` far EARLIER
    (`2020-01-01...`) than the Thread's current `last_message_at` --
    value unchanged (no regression), confirmed by direct frontmatter read.
  - Re-ran again with a `received` genuinely LATER (`2099-01-01...`) --
    value correctly advanced, confirmed by direct frontmatter read.
  - Message file count stayed at 100 across all 3 additional calls --
    zero duplicates, confirming idempotency is real and governed by the
    identity-field match, not accidental.
- (Unlabeled, supporting) **PASS, reconfirmed.** `ensure_bare_person_note`'s
  own real behavior confirmed byte-for-byte unchanged a second time: all
  156 real Person notes from this fresh sample are SHA-256-identical
  between the migrated and true-baseline runs.

**Verification technique note:** `PYTHONIOENCODING=utf-8` had to be set
explicitly on the driver's own subprocess calls -- a real email in the
100-email sample contains a non-UTF-8-decodable byte under Windows'
default console codepage when captured via plain `text=True` subprocess
capture (the same class of issue `list_recent_emails.py`'s own docstring
already documents and works around for ITS OWN stdout, but `ingest_email.py`
itself has no such guard on ITS OWN stdout -- worth a future, separate,
disclosed hardening pass, not fixed here as it's outside this task's own
scope and did not block real verification, only required a driver-side
workaround).

**Files touched beyond this task's original `## Files to Modify`
(operator-directed, ESC-061 resolution -- see the updated `## Files to
Modify` section above for the full list):** `Hermes-Provisioning/shared/
vault_manager.py`, `Hermes-Provisioning/shared/tests/test_vault_manager.py`,
plus a resync (content-only, mechanical `Copy-Item` from the canonical
source, no manual edits) of 10 other repo copies and 73 live Hermes
profile copies.

**Scratch artefacts cleaned up:** `C:\scratch-sb87t01\` (both scratch
vaults, the 100-email sample, the driver/compare scripts, all results
JSON) removed after verification completed -- nothing left behind outside
this repo.

**Escalations / review-queue resolution:**
- `ESCALATIONS.md` → `ESC-061` marked **Resolved** (see its own updated
  entry -- resolving artefact: this task's own completion, commit to
  follow).
- `REVIEW-QUEUE.md` → the `REQ-SB-87-US-02-T01` entry removed (resolved,
  task now `Done`); a NEW entry added naming the one remaining disclosed
  judgement call (RawMessage filename-convention divergence) for human
  spot-check ahead of `T05`'s own future real-vault cutover.

**Task marked `Done`.** `AC-01` and `AC-02` (this task's own two locked
ACs) both verified with a real, live positive result against a real
~100-email scratch-vault sample. `gate: flagged` (not `clear`) --
one disclosed scope-internal judgement call (the filename-convention
divergence) needs human spot-check before `T05`'s own future real-vault
cutover, per this project's own established "log it, don't block, flag
the task's gate" pattern. `T02`-`T05` remain untouched, `Ready`, not
started by this task.
