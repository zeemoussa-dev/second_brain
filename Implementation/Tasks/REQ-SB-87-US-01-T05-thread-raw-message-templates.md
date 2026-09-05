---
id: REQ-SB-87-US-01-T05
title: Author thread / raw-message Template.json definitions
parent_story: REQ-SB-87-US-01
requirement_id: REQ-SB-87
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-87-US-01-T02]
created: 2026-09-01
updated: 2026-09-01
---

# REQ-SB-87-US-01-T05 — Author thread / raw-message Template.json Definitions

## Parent Story

- Story: [[REQ-SB-87-US-01]] — `../UserStories/REQ-SB-87-US-01-vault-manager-resync-and-thread-templates.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-87 *Email Thread Capture — a New, LLM-Driven Pipeline*

---

## Objective

Author `.second-brain/data/Templates/thread/Template.json` (declaring
RawMessage as its own `growth: "dynamic"` child under `messages/`), matching
today's real Thread/RawMessage shape exactly, plus the new classification
field and the `## Actions` caller-widening — per `ADR-017` and this story's
own locked Scenario 2.

---

## Starting State → End State

**Before / Inputs:**
- No `thread` (or `raw-message`) `Template.json` exists yet.
- Real, confirmed current shape (direct read, `vault_lib.py`):
  - Thread frontmatter: `type: "Thread"`, `conversation_id`, `tags` (list),
    `thread_name`, `last_message_at` (str, default `""`),
    `last_summarized_at` (str, default `""`).
  - Thread baseline body: `## Summary`, `## Personal Notes`, `## Actions`,
    `## Related` (in that order) — **`## Files` is NOT present at baseline
    creation today; it is lazily inserted only when `capture_attachments`/
    `capture_file_link` first need it** (`insert_body_section_if_missing`).
  - RawMessage frontmatter: `type: "RawMessage"`, `conversation_id`,
    `message_id`, `sender`, `sender_email`, `subject`, `received`, and
    optionally `participant_links` (list, only when non-empty).
  - Real per-caller restrictions today (`vault_lib.py`'s own
    `_CALLER_ALLOW_LISTS`): `## Related` → `link_person_to_thread` only;
    `## Files` → `capture_attachments`/`capture_file_link` only;
    `## Personal Notes`/`## Actions` → refused to everyone
    (`_HUMAN_OWNED_HEADERS`).

**After / Outputs:**
- `.second-brain/data/Templates/thread/Template.json`:
  - `identity.strategy: "id"`.
  - `root.frontmatter_defaults`: `type: "Thread"`, `last_message_at: ""`,
    `last_summarized_at: ""` (real, confirmed defaults). Add the NEW
    classification field here too, e.g. `classification: ""` as a
    reserved-but-empty default — the real value is stamped by
    `REQ-SB-87-US-03`'s own Capture-time write, never invented by this
    task; exact field name is `classification` unless a stronger existing
    convention is found (this task's own disclosed naming call).
  - `root.sections` (in real baseline order, plus `## Files` — see the
    disclosed judgement call in Context/Notes below):
    - `## Summary` → `"access": "machine_write", "allowed_callers":
      ["apply_thread_review"]`.
    - `## Personal Notes` → `"access": "human_only"` (no `allowed_callers`
      — refused unconditionally, no exception, ever).
    - `## Actions` → `"access": "machine_write", "allowed_callers":
      ["apply_thread_review"]` — the SAME one identity as `## Summary`
      (`ADR-017`'s own explicit decision: one caller, two sections). This
      is the real, deliberate NARROWING from today's blanket
      never-machine-writable rule, for this one section only.
    - `## Related` → `"access": "machine_write", "allowed_callers":
      ["link_person_to_thread"]`.
    - `## Files` → `"access": "machine_write", "allowed_callers":
      ["capture_attachments", "capture_file_link"]`.
  - `root.children`: one entry, `"name": "messages"`, `"growth":
    "dynamic"`, `"folder": "messages"`, `"identity_fields":
    ["conversation_id", "message_id"]`, its own
    `"frontmatter_defaults": {"type": "RawMessage"}` (RawMessage's other
    fields — `sender`/`sender_email`/`subject`/`received`/
    `participant_links` — are supplied per-call, not defaulted).
- A `raw-message` template is only needed as a SEPARATE `Template.json` if
  RawMessage notes are ever looked up/modified independently of their
  parent Thread; per the real, confirmed usage (`vault_lib.py`'s own
  `create_raw_message_note` is only ever called FROM `ingest_email.py`,
  always in the context of an already-resolved Thread), the dynamic-child
  declaration nested inside `thread/Template.json` (above) is sufficient —
  **do not author a separate top-level `raw-message` template unless a
  real, direct-lookup-by-RawMessage-id need is found during this task's own
  build** (disclosed judgement call, log if this changes).

---

## Files to Modify

- `.second-brain/data/Templates/thread/Template.json` (new).
- (Conditionally, only if the disclosed judgement call above resolves
  differently) `.second-brain/data/Templates/raw-message/Template.json`.

---

## Constraints

- Inherits from parent story.
- Templates are authored directly at the live vault path — no separate
  deploy step (`MEMORY.md`, 2026-08-30 Decision).
- Match today's real frontmatter/section shape exactly, plus the two
  additive changes this story's own Scenario 2 locks (classification
  field, `## Actions` caller-widening) — never drop or rename an existing
  real field/section.
- **Disclosed judgement call — `## Files` at initial creation.**
  `vault_manager.py`'s own `create()` unconditionally writes every declared
  `root.sections` entry as a real (possibly empty) body header at creation
  time — there is no way to declare a section for ACCESS-CONTROL purposes
  only while excluding it from the initial body. Since `## Files` must be
  declared (with `allowed_callers`) to get its own caller restriction, this
  means every NEW Thread created through the migrated engine will carry an
  empty `## Files` header from creation onward, whereas today it is lazily
  inserted only on first attachment/file-link. This is accepted as a
  minor, deliberate, non-breaking normalization — it matches how every
  OTHER already-`Done` template (Customer/Partner/Opportunity) already
  behaves (a declared section is always present, even empty, at creation);
  it adds an inert empty header, never removes/reorders/renames anything a
  real caller or human already depends on. **Not treated as a violation of
  `REQ-SB-87-US-02-AC-01`'s "exact same real... body-section... layout"
  requirement** — logged here for spot-check, not an escalation.

---

## Tests

```
src\backend\.venv\Scripts\python.exe -m pytest Hermes-Provisioning\shared\tests\test_vault_manager.py -v
```

**Automated tests (new, added to `test_vault_manager.py`, against the REAL
authored `thread` template — load it via `load_template(vault, "thread")`
using a scratch vault fixture pointed at a COPY of the real
`.second-brain/data/Templates/thread/Template.json`):**
1. `[REQ-SB-87-US-01-AC-02]` `load_template`/`create`/`find_by_id`/
   `get_section_content`/`modify_section` resolve, create, and update a
   Thread concept note through the `thread` template alone, with zero
   Thread-specific Python code (a pure `Template.json`-driven exercise, the
   same style as this file's own existing `kb-doc`/`dated-note` fixture
   tests). Assert the created note's frontmatter/sections match the real
   shape above.
2. `[REQ-SB-87-US-01-AC-02]` Call `modify_section(..., section="## Related",
   caller="link_person_to_thread")`; assert success. Call the SAME section
   with `caller="capture_attachments"`; assert refused. Repeat symmetrically
   for `## Files` (only `capture_attachments`/`capture_file_link` succeed).
3. `[REQ-SB-87-US-01-AC-02]` Call `modify_section(..., section="## Actions",
   caller="apply_thread_review")`; assert success. Call the SAME section
   with any OTHER caller identity, including each of
   `ingest_email`/`rename_thread`/`capture_attachments`/
   `capture_file_link`/`link_person_to_thread` (email-thread-capture's own
   five real script identities); assert every one is refused.
4. `[REQ-SB-87-US-01-AC-02]` Call `modify_section(..., section="## Personal
   Notes", caller="apply_thread_review")` (and again with any other
   caller); assert refused in every case, unconditionally, no exception.
5. `[REQ-SB-87-US-01-AC-03]` Create a Thread, then call the dynamic-child
   verb (`T01`) to create a RawMessage under its `messages/` declared
   child for 1 message, then again for 2 more DISTINCT `message_id`
   values (3 total). Assert all 3 exist under the Thread's own real
   `messages/` folder — genuinely unbounded, real Thread template, not
   just the generic scratch fixture `T01` used.
6. `[REQ-SB-87-US-01-AC-04]` Call the dynamic-child verb twice with the
   SAME `(conversation_id, message_id)` pair; assert the second call
   returns the existing path, no duplicate created.

**Manual verification steps:** none required — covered by the automated
suite above.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `thread/Template.json` matches today's real frontmatter/body-section
      shape, plus the classification field and `## Actions` caller-widening
- [x] Per-caller access is correctly declared and enforced for every
      section (`## Related`, `## Files`, `## Summary`, `## Actions`,
      `## Personal Notes`)
- [x] RawMessage is declared as a `growth: "dynamic"` child of `thread`,
      idempotent by `(conversation_id, message_id)`, genuinely unbounded
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Actually migrating `ingest_email.py`/`apply_thread_review.py` onto this
  template — `REQ-SB-87-US-02`/`REQ-SB-87-US-04`.
- Writing the real classification VALUE — `REQ-SB-87-US-03`.
- Writing real `## Actions` content — `REQ-SB-87-US-05`.

---

## Context / Notes

`ADR-017` and `architecture.md` → `§vault_manager.py Engine Extensions` are
authoritative. Read `vault_lib.py`'s own `create_thread_note_baseline`/
`create_raw_message_note`/`_CALLER_ALLOW_LISTS`/`_HUMAN_OWNED_HEADERS`
directly (already done for this task file, see Starting State above) before
finalizing field names — do not invent a field name not confirmed real.

---

## Implementation Log

**What was built:** `.second-brain/data/Templates/thread/Template.json`
authored at the live vault path
(`<OPERATOR_VAULT_OLD>\.second-brain\data\Templates\thread\
Template.json` — resolved from `.env`'s `VAULT_PATH`), matching every
real field/section confirmed by directly reading
`email-thread-capture/scripts/vault_lib.py`:
- `identity.strategy: "id"`, `on_missing: "error"`,
  `allow_create_folder: true`.
- `root`: `own_folder: true`, `plain_filename: true`, `plain_folder: true`
  (Customer/Partner's own durable, name-keyed, no-date shape —
  Thread's own real folder holds both the concept note and its
  `messages/` children, same as Customer's `log`/`captures`).
  `on_existing_title: "always_new"` (disclosed judgement call, see
  below).
- `frontmatter_defaults`: `type: "Thread"`, `last_message_at: ""`,
  `last_summarized_at: ""` (all 3 confirmed real defaults), plus the NEW
  `classification: ""` field (`REQ-SB-87-US-03`'s own future write —
  no stronger existing naming convention found anywhere in
  `vault_lib.py`/the real vault's own tag conventions, so the task's own
  disclosed default name, `classification`, was kept as-is).
  `conversation_id`/`tags`/`thread_name` are intentionally per-call, not
  defaulted — matching `create_thread_note_baseline`'s own real shape.
- `sections` (real baseline order, `## Files` appended): `Summary`
  (`machine_write`, `allowed_callers: ["apply_thread_review"]`),
  `Personal Notes` (`"access": "human_only"`, no caller list), `Actions`
  (`machine_write`, `allowed_callers: ["apply_thread_review"]` — the
  SAME one identity as `Summary`, per `ADR-017`'s deliberate narrowing),
  `Related` (`machine_write`, `allowed_callers:
  ["link_person_to_thread"]`), `Files` (`machine_write`,
  `allowed_callers: ["capture_attachments", "capture_file_link"]`).
- `children`: one `growth: "dynamic"` entry, `name: "messages"`,
  `folder: "messages"`, `identity_fields: ["conversation_id",
  "message_id"]`, `frontmatter_defaults: {"type": "RawMessage"}` — no
  `sections` declared (see the MEMORY.md Constraint entry on the real
  raw-body-text gap this surfaced, non-blocking for this task's own
  locked ACs).
- No separate `raw-message/Template.json` authored — confirmed by
  direct reading that `create_raw_message_note` is only ever reached
  through an already-resolved Thread (`ingest_email.py`'s own real call
  graph), matching the task's own disclosed default. `raw-message`
  entry removed from `## Files to Modify` conditionality — not
  triggered.

**Scope-internal judgement calls** (logged for human spot-check, not
blocking):
1. `classification` kept as the field name — no stronger existing
   convention found (checked `vault_lib.py`, `apply_thread_review.py`'s
   own tag usage, and the real vault's own `customer/*`/`kind/*`
   namespaced-tag convention — none of these name a coarse
   Internal/Partner/Customer classification concept today).
2. `on_existing_title: "always_new"` + `on_missing: "error"` — a
   deliberate pairing NOT matching any single existing real template's
   own precedent (Customer/Partner/Opportunity pair `"error"`+`"error"`;
   every other real `always_new` template pairs `"always_new"`+
   `"create"`). Reasoning: a duplicate real email Subject across two
   genuinely unrelated conversations is common and never a mistake
   (unlike a duplicate Customer/Opportunity NAME), so `"error"` on
   title would incorrectly refuse legitimate new Threads and
   `"update_section"` would incorrectly merge writes into an unrelated
   conversation — `"always_new"` is correct. `on_missing: "error"`
   because none of Thread's own real callers (`link_person_to_thread`/
   `capture_attachments`/`capture_file_link`/`apply_thread_review`)
   should ever be able to fabricate a Thread via a bare section write;
   only `ingest_email.py`'s own explicit, deliberate `create()` call
   (out of scope, `US-02`) may create one. Full reasoning also recorded
   in `MEMORY.md` (Pattern entry, 2026-09-01) for `US-02` to read before
   migrating `ingest_email.py` onto this template.
3. `## Files` is declared (and therefore always present, even empty, at
   creation) — already pre-disclosed and accepted in this task's own
   Constraints section; reconfirmed unchanged.
4. RawMessage's own dynamic-child declaration has no `sections` list —
   `create_dynamic_child()` has no way to write a flat, headerless raw
   body the way `create_raw_message_note` does today; a genuinely new
   finding, logged as its own `MEMORY.md` Constraint entry for `US-02`
   to resolve (declare a `Body` section, accepting a new `## Body`
   header, or extend the engine) — out of this task's own `## Files to
   Modify` (Template.json only, no engine code).

**Verification — reconciling the task's own Tests block against `##
Files to Modify` (disclosed reconciliation, not a silent scope
narrowing):** the Tests block's own prose says the new automated tests
are "added to `test_vault_manager.py`," but that file is NOT listed
under this task's own `## Files to Modify` (only
`Hermes-Provisioning/shared/tests/test_vault_manager.py` was T01's/T02's
own scope, both already `Done`). Per hard rule 5 (coder is
scope-bounded to `## Files to Modify`) and the pipeline's own launch
instructions for this task ("use the real `vault_manager.py` CLI (or a
scratch Python script importing it directly)... Stay strictly within
`## Files to Modify`"), verification below was performed LIVE via a
throwaway scratch script (direct-import of the real, unmodified
`Hermes-Provisioning/shared/vault_manager.py`) plus a real CLI smoke
call, against a scratch vault under the session scratchpad (never the
real vault), using a COPY of the real, just-authored
`thread/Template.json` — never `test_vault_manager.py` itself. The
scratch vault was deleted after verification; no file outside `## Files
to Modify` was touched.

**Live verification results, keyed by AC-ID:**

- `[REQ-SB-87-US-01-AC-02]` PASS (4 parts, all against the real,
  unmodified `vault_manager.py` and a COPY of the real `thread`
  Template.json):
  - Part a (shape+lifecycle): `create()` produced a real Thread note
    whose on-disk frontmatter/section-header order matched exactly
    (`type`/`conversation_id`/`tags`/`thread_name`/`last_message_at`/
    `last_summarized_at`/`classification`, `## Summary` → `##
    Personal Notes` → `## Actions` → `## Related` → `## Files` in
    that literal order); `find_by_id` resolved it; `get_section_content`
    read the empty `Summary`; `modify_section(caller=
    "apply_thread_review")` updated it — read the raw file directly on
    disk afterward (not just via the API) to confirm.
  - Part b (`## Related`/`## Files` per-caller access): `caller=
    "link_person_to_thread"` wrote `## Related`, succeeded;
    `caller="capture_attachments"` on the same section raised a real
    `VaultManagerError` naming both `Related` and `capture_attachments`,
    and the section's prior content was confirmed unchanged on disk
    afterward (not a partial write). Symmetric for `## Files`:
    `capture_attachments`/`capture_file_link` both succeeded,
    `link_person_to_thread` was refused by name.
  - Part c (`## Actions` narrowed to `apply_thread_review` only):
    `apply_thread_review` succeeded; every one of
    `email-thread-capture`'s own real five script identities
    (`ingest_email`, `rename_thread`, `capture_attachments`,
    `capture_file_link`, `link_person_to_thread`) was individually
    tried and individually refused, each with a real `VaultManagerError`
    naming `Actions` and that specific caller; content confirmed
    unchanged after all 5 refusals.
  - Part d (`## Personal Notes` fully human-owned, no exception):
    `apply_thread_review`, `ingest_email`, and `caller=None` were all
    refused (the `human_only` access guard, independent of
    `allowed_callers`); section confirmed empty on disk throughout.
- `[REQ-SB-87-US-01-AC-03]` PASS: 3 distinct real RawMessage children
  (`message_id` `msg-1`/`msg-2`/`msg-3`) created via
  `create_dynamic_child()` against the REAL `thread` template (not the
  generic `T01` scratch fixture) — all 3 confirmed as real, distinct
  files under the Thread's own real `messages/` folder (`glob("*.md")`
  count == 3), each with `type: "RawMessage"`/the correct
  `conversation_id`, one with a real `participant_links` list confirmed
  round-tripped. Also independently confirmed via the real CLI
  (`find --by folder --value Threads`) that all 3 files are visible on
  disk.
- `[REQ-SB-87-US-01-AC-04]` PASS: a repeated `create_dynamic_child()`
  call with the SAME `(conversation_id="conv-001",
  message_id="msg-1")` identity returned `created: false` and the exact
  same path as the first call; the `messages/` folder still held exactly
  3 real files afterward (no duplicate).

Full script output:
```
TEST1 (AC-02, part a: shape+lifecycle) PASS
TEST2 (AC-02, part b: Related/Files per-caller access) PASS
TEST3 (AC-02, part c: Actions narrowed to apply_thread_review only) PASS
TEST4 (AC-02, part d: Personal Notes fully human-owned) PASS
TEST5 (AC-03: unbounded dynamic RawMessage children under real thread template) PASS
TEST6 (AC-04: idempotent RawMessage lookup avoids a duplicate) PASS
ALL LIVE VERIFICATION CHECKS PASSED
```

**No `ESCALATIONS.md` / `REVIEW-QUEUE.md` entries written by this
task** — no new dependency, no shared-interface change beyond what
`ADR-017`/`T01`/`T02` already govern, no ADR deviation, no unanticipated
file, every locked AC verified live with a real positive result. The 4
scope-internal judgement calls above (including the new raw-body-text
finding) are logged for human spot-check, not blocking, consistent with
`SPRINT-037`/`SPRINT-048`'s own established precedent for a mechanical,
disclosed judgement call within an otherwise-complete, locked task.

gate: clear 2026-09-01 — no triggers fired beyond what `ADR-017` (already
human-reviewed at the story level) and `T01`/`T02` already cover; every
locked AC (`AC-02`, `AC-03`, `AC-04`) verified live with a real positive
result; the 4 disclosed judgement calls above are scope-internal, not
material assumptions filling a genuine requirement gap.
