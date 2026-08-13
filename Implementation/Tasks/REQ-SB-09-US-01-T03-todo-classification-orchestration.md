---
id: REQ-SB-09-US-01-T03
title: New app/business/todo_classification.py orchestration module + new compass_client.classify_task
parent_story: REQ-SB-09-US-01
requirement_id: REQ-SB-09
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-09-US-01-T01, REQ-SB-09-US-01-T02]
created: 2026-08-13
updated: 2026-08-13
---

# REQ-SB-09-US-01-T03 — New todo_classification.py orchestration module + classify_task

## Parent Story

- Story: [[REQ-SB-09-US-01]] — `../UserStories/REQ-SB-09-US-01-todo-notes-from-outlook-tasks-capture.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-09 *To-Do Task Capture Pipeline*

---

## Objective

Add the single shared "fetch Outlook Tasks → classify each by customer via
Compass → write/top-up the Task note through the EntryID-keyed dedup index
→ link the matched customer hub after a confirmed match only"
orchestration (`ADR-027`), plus the new, customer-only
`compass_client.classify_task` its customer derivation depends on.

---

## Starting State → End State

**Before / Inputs:**
- `T01` added `outlook_com.list_outlook_tasks`. `T02` added the Task-note
  vault_writer primitives, including the `task_note_index.json` dedup
  lookup.
- `app/business/customer_hub_linking.py` already exposes
  `ensure_customer_hub_note(customer)`/`link_note_to_customer_hub(note_path,
  customer)` (the granular primitives, reused as-is — never
  `ensure_hub_note_and_link`, per the same carve-out
  `meeting_classification.py`/`people_extraction.py` established).
- `app/data_access/compass_client.py` has `classify_email` (a combined
  customer+kind, sender-framed classifier) but no Task-shaped, customer-
  only classifier.

**After / Outputs:**
- `app/data_access/compass_client.py` gains a new `classify_task`
  function, alongside `classify_email`.
- A new file, `app/business/todo_classification.py`, exposing
  `classify_recent_todos`.

---

## Files to Modify

- `src/backend/app/data_access/compass_client.py`:

  Append at the end of the file (after `classify_email`):
  ```python
  def classify_task(
      subject: str,
      body: str,
      known_customers: list[str],
  ) -> dict:
      """Customer-only sibling to classify_email (ADR-027 point 4) -- a
      Task has no sender and needs no `kind` axis (its folder placement
      is fixed, Work/Tasks/, never Compass-classified), so reusing
      classify_email as-is would force a discarded kind guess into every
      call and misrepresent an absent sender inside a prompt worded
      around "inbox item"/`From:` framing designed for email. Same
      "Unsorted rather than guessing" fallback posture as classify_email."""
      customer_list = ", ".join(known_customers) if known_customers else "(none yet)"
      prompt = (
          "Classify which customer/company this to-do task relates to. "
          "Respond with a single JSON object: {\"customer\": <name>, "
          "\"confidence\": <0-1 float>}.\n\n"
          f"Already known customers: {customer_list}. Reuse an exact "
          "existing name (same spelling/casing) when it clearly matches "
          "one. If it clearly relates to a real customer/company not yet "
          "in that list, propose a concise proper-noun name — new "
          "customers are expected. If you can't confidently tell, use "
          "\"Unsorted\" rather than guessing.\n\n"
          f"Task subject: {subject}\n\n{body[:4000]}"
      )
      payload = {
          "model": settings.compass_model,
          "messages": [{"role": "user", "content": prompt}],
      }
      headers = {
          "Authorization": f"Bearer {settings.compass_api_key}",
          "Content-Type": "application/json",
      }
      try:
          response = httpx.post(
              settings.compass_base_url, headers=headers, json=payload, timeout=30.0
          )
          response.raise_for_status()
      except httpx.HTTPError as exc:
          raise CompassError(f"Compass call failed: {exc}") from exc

      data = response.json()
      try:
          content = data["choices"][0]["message"]["content"]
          parsed = json.loads(content)
          return {
              "customer": parsed.get("customer") or "Unsorted",
              "confidence": float(parsed.get("confidence", 0.0)),
          }
      except (KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
          raise CompassError(f"couldn't parse Compass response: {exc}") from exc
  ```

- `src/backend/app/business/todo_classification.py` (new file):

  ```python
  """Orchestrates the To-Do (Outlook Tasks) capture pipeline (REQ-SB-09):
  fetch Outlook Tasks, classify each by customer via Compass
  (classify_task, customer-only, ADR-027), write/top-up the Task note
  through the EntryID-keyed dedup index (ADR-027 point 3 -- consulted
  BEFORE any path is computed from current Outlook fields, a genuine
  divergence from meeting_classification.py's own recompute-and-exists()
  mechanism), link the matched customer hub after a confirmed match only.
  """
  from __future__ import annotations

  from datetime import datetime
  from pathlib import Path

  from app.business import customer_hub_linking
  from app.data_access import compass_client, outlook_com, vault_writer

  _UNSORTED_CUSTOMER = "Unsorted"


  def classify_recent_todos(limit: int = 100) -> list[dict]:
      """The shared "ensure this Outlook Task's Task note exists and is
      up to date" operation -- called once per fetched task, every run.
      The task_note_index lookup (vault_writer.lookup_task_note_stem) is
      what prevents duplicate notes (Scenario 2, 6, 7), consulted BEFORE
      any filename is computed -- unlike meeting_classification.py, this
      module never recomputes a path from current field values and
      exists()-checks it."""
      tasks = outlook_com.list_outlook_tasks(limit=limit)
      known_customers = vault_writer.list_known_customers()
      results: list[dict] = []

      for task in tasks:
          try:
              classification = compass_client.classify_task(
                  subject=task["subject"],
                  body=task["body"],
                  known_customers=known_customers,
              )
          except compass_client.CompassError as exc:
              results.append({"subject": task["subject"], "error": str(exc)})
              continue

          customer = classification["customer"]
          if customer == _UNSORTED_CUSTOMER:
              # Task's own resolved schema requires an absent customer
              # field (not a written "Unsorted" placeholder) when no
              # confident match exists (Scenario 3) -- a deliberate
              # divergence from email's own "Unsorted" written as a real
              # customer value.
              customer = None

          existing_stem = vault_writer.lookup_task_note_stem(task["id"])
          if existing_stem:
              note_path = Path(vault_writer.task_note_path_for_stem(existing_stem))
              vault_writer.ensure_task_note_baseline_frontmatter(
                  note_path, task["subject"], customer, task["due"], task["status"], task["id"],
              )
              created = False
          else:
              capture_date = datetime.now().date().isoformat()
              stem = vault_writer.task_note_filename_stem(task["subject"], capture_date, task["id"])
              note_path = Path(vault_writer.create_task_note_baseline(
                  task["subject"], customer, task["due"], task["status"], task["id"], capture_date,
              ))
              vault_writer.record_task_note(task["id"], stem)
              created = True

          linked = False
          if customer:
              customer_hub_linking.ensure_customer_hub_note(customer)
              linked = customer_hub_linking.link_note_to_customer_hub(note_path, customer)

          results.append({
              "subject": task["subject"],
              "note_path": str(note_path),
              "created": created,
              "customer": customer,
              "status": task["status"],
              "linked": linked,
          })

      return results
  ```

---

## Constraints

- Inherits from parent story (`ADR-003` layering: no HTTP, no direct
  filesystem I/O — every read/write goes through `vault_writer`,
  `outlook_com`, `compass_client`, or `customer_hub_linking`; idempotency
  is load-bearing, real live vault and real live Outlook Tasks folder).
- Must NOT modify `people_extraction.py`, `customer_hub_linking.py`,
  `outlook_com.py`, `vault_writer.py`, `meeting_classification.py`, or
  `email_classification.py` — this task only adds the new module and the
  new `compass_client` function.
- Must call `customer_hub_linking.ensure_customer_hub_note` and
  `customer_hub_linking.link_note_to_customer_hub` directly — never
  `customer_hub_linking.ensure_hub_note_and_link` — and only after a
  confirmed (non-`None`, non-`"Unsorted"`) customer match. Load-bearing
  carve-out from the parent story's own Constraints.
- Compass's own `"Unsorted"` sentinel must be translated to `None` before
  it reaches `vault_writer.create_task_note_baseline`/
  `ensure_task_note_baseline_frontmatter` or `customer_hub_linking` — the
  resolved schema requires an ABSENT `customer` key on a no-match, not a
  written `"Unsorted"` value (Scenario 3), a deliberate divergence from
  `email_classification.py`'s own "Unsorted" written as a real customer
  value.
- `vault_writer.lookup_task_note_stem` must be consulted BEFORE any
  filename is computed for a given task — never recompute-then-`exists()`
  check the way `meeting_classification.py` does (`ADR-027` point 3's own
  load-bearing divergence).
- `vault_writer.record_task_note` must be called ONLY on first creation
  (the `else` branch above), never on top-up — a stem is never
  reassigned once recorded.

---

## Tests

<!-- This task's own function carries most of this story's locked ACs,
verified directly (Python shell, no manual /poc endpoint for this story --
the story's own pre-sketched task table names none, and every prior
capture-pipeline task in this codebase already establishes direct-call
verification as sufficient, e.g. REQ-SB-35-US-01's own Learnings entry).
AC-04 (scheduler wiring) is T04's own. AC-08 (My Day) is T06's own. -->

**Manual verification steps** (all against the real live Outlook Tasks
folder and the real live vault, `.venv\Scripts\python.exe`, cwd
`src/backend`):

1. **[REQ-SB-09-US-01-AC-01]** Ensure at least one real Outlook Task
   exists whose subject/body content clearly names a known customer (or
   temporarily add one via the Outlook desktop client). Call
   `todo_classification.classify_recent_todos(limit=100)`. Confirm the
   corresponding result has `created: True` (first run) and a real
   `customer` value; open the written note under `Work/Tasks/` and
   confirm its frontmatter has `type: "Task"`, `subject`, `status`, a
   `due` key only if the real task has one set, `tags` including
   `customer/<slug>` and `kind/task`, `source: "outlook-task"`,
   `outlook_entry_id`, and its body starts with
   `**Customer:** [[<Hub>]]`.
2. **[REQ-SB-09-US-01-AC-02]** Re-run `classify_recent_todos()` a second
   time with no Outlook-side changes. Confirm the same task's result now
   has `created: False`, no new file was created under `Work/Tasks/`
   (file count unchanged), and the existing note's content is
   byte-for-byte unchanged (confirmed via `LastWriteTime`, not just
   absence of an error) — the lookup found it via
   `vault_writer.lookup_task_note_stem`, not by recomputing its filename.
3. **[REQ-SB-09-US-01-AC-03]** Find (or temporarily create) a real
   Outlook Task whose subject/body content matches no known customer.
   Run `classify_recent_todos()`. Confirm the resulting note's frontmatter
   has NO `customer` key at all (not `""`), its `tags` is exactly
   `["kind/task"]`, its body has no `**Customer:**` line, and no new
   `Work/Customers/` hub note was created as a side effect.
4. **[REQ-SB-09-US-01-AC-05]** Mark a real Outlook Task's Complete flag
   (via the Outlook desktop client). Run `classify_recent_todos()`.
   Confirm the resulting note's `status` frontmatter reads
   `"Completed"`, and confirm the task is present in the results list
   with `created` reflecting whether this was a new or existing note —
   never silently absent from the results.
5. **[REQ-SB-09-US-01-AC-06] (also the end-to-end live EntryID-stability
   confirmation `ADR-027`'s Consequences section requires — not a
   code-review-level check):** on a real Outlook Task note already
   captured by step 1/2 above, manually add a line of content to the
   note's body BELOW the auto-generated header (simulating the user's
   own notes). In the real Outlook desktop client, edit that same task's
   due date AND status. Run `classify_recent_todos()` again. Confirm: (a)
   the manually-added body content is byte-for-byte preserved; (b) the
   note's `due`/`status` frontmatter now reflect the NEW Outlook values,
   not the stale ones; (c) `created` is `False` for this task in the
   results — this is genuinely the SAME note topped up, not a new
   duplicate note under `Work/Tasks/` (confirmed via file count and
   `note_path` matching the original); (d) the note's own
   `outlook_entry_id` frontmatter value is unchanged, confirming the
   task's `EntryID` itself held stable across the Outlook-side edit in
   the context of the full pipeline (reinforcing `T01`'s own isolated
   check).
6. **[REQ-SB-09-US-01-AC-07]** Create two real (or temporarily-created,
   throwaway) Outlook Tasks sharing the identical subject text. Run
   `classify_recent_todos()`. Confirm two DISTINCT notes are created
   under `Work/Tasks/` (different filenames, disambiguated by each
   task's own entry-id suffix), and neither note's content was
   overwritten by the other's write. Clean up any throwaway Outlook Tasks
   and their resulting notes/index entries afterward, restoring the vault
   and mailbox to their pre-task state (or leave real production data in
   place per this project's own "real data is fine to keep" precedent,
   noting the choice in the Implementation Log).

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `classify_task` returns `{"customer", "confidence"}` from a
      customer-only, sender-free prompt, falling back to `"Unsorted"`
      rather than guessing
- [ ] `classify_recent_todos` creates a baseline Task note when
      `lookup_task_note_stem` finds no existing entry, tops it up (never
      overwriting user body content) when it does, and only calls
      `customer_hub_linking`'s two granular primitives (never
      `ensure_hub_note_and_link`) after a confirmed, non-`"Unsorted"`
      customer match
- [ ] `"Unsorted"` from Compass is translated to `None` before it reaches
      any vault-writer primitive or `customer_hub_linking`
- [ ] `record_task_note` is called only on first creation, never on
      top-up
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Wiring `classify_recent_todos` into the recurring scheduler tick, or
  the working-mode gate — that is `T04`.
- The manual on-demand trigger endpoint — none is built for this story
  (unlike Meeting's own `/poc/classify-meetings`); this task's own
  `## Tests` verify directly via Python shell, matching this codebase's
  own established "prefer direct verification over spinning up the full
  HTTP server" precedent (`Implementation/Learnings.md`).

---

## Context / Notes

Mirrors `meeting_classification.py`'s existing shape: a single business
module composing another business module (`customer_hub_linking`),
calling only into `vault_writer`/`outlook_com`/`compass_client` (never
doing filesystem/COM I/O itself), returning a per-task results list.

---

## Implementation Log (built 2026-08-13)

`compass_client.classify_task` and `app/business/todo_classification.py`
(`classify_recent_todos`) built exactly per spec. Verified live against
the real Outlook Tasks folder, real Compass, and the real vault
(`.venv\Scripts\python.exe`, cwd `src/backend`).

**[REQ-SB-09-US-01-AC-01] PASS.** Ran `classify_recent_todos(limit=25)`
against the real Tasks folder (77.3s, 25 real items). A real task
("Naima/Moussa (Masdar Sync)") matched customer "Masdar": frontmatter
`type: "Task"`, `subject`, `status: "Not Started"`, no `due` (Outlook
had none set), `tags: ["customer/masdar", "kind/task"]`,
`source: "outlook-task"`, `outlook_entry_id`, body starts
`**Customer:** [[Masdar]]`. A genuinely NEW customer, "G42" (not
previously in `list_known_customers()`), was also correctly proposed by
Compass and correctly created a new `Work/Customers/G42.md` hub note
plus the wikilink — confirms the taxonomy-extensibility path, not just
the already-known-customer path.

**[REQ-SB-09-US-01-AC-02] PASS.** Re-ran `classify_recent_todos()`
scoped (via a real-data-filtered, in-process monkeypatch of
`outlook_com.list_outlook_tasks` — the established technique for
bounding a live check to a real subset without a second full-folder
sweep) to one already-captured real task with zero Outlook-side change.
`created: false`; the note's bytes and `mtime` were BYTE-IDENTICAL
before/after (true no-op); `Work/Tasks/` file count unchanged
(25 → 25). Lookup found it via `lookup_task_note_stem`, not a
recomputed path.

**[REQ-SB-09-US-01-AC-03] PASS.** Multiple real tasks with no customer
match (e.g. "Request for Submission of Bank Details for Payroll
Processing") produced frontmatter with NO `customer` key at all (not
`""`), `tags` exactly `["kind/task"]`, no `**Customer:**` body line, and
no new `Work/Customers/` hub note as a side effect.

**[REQ-SB-09-US-01-AC-05] PASS.** Created a real throwaway Outlook Task,
marked `Complete = True` via real COM, ran the real (monkeypatch-bounded
to this one item) capture. Resulting note: `status: "Completed"`,
present in the results list with `created` reflecting the real
create/top-up state — never silently absent or left stale.

**[REQ-SB-09-US-01-AC-06] PASS — also the mandated end-to-end live
`EntryID`-stability reinforcement.** On the same real throwaway task
(already captured), manually added
`"MANUALLY ADDED USER CONTENT — must survive top-up."` below the
auto-generated header. Edited that same real item's due date AND
Complete flag via real COM. Re-ran capture (same bounded technique).
Confirmed: (a) the manually-added body line survived byte-for-byte;
(b) `due`/`status` frontmatter updated to the NEW Outlook values
(`due: "2026-08-16 00:00:00+00:00"`, `status: "Completed"`); (c)
`created: false` — same note (`note_path` matched exactly, file count
unchanged) topped up, not duplicated; (d) `outlook_entry_id` unchanged
— `EntryID` held stable across the Outlook-side edit inside the full
pipeline, reinforcing `T01`'s own isolated check.

**[REQ-SB-09-US-01-AC-07] PASS (mechanism), plus one real, disclosed,
non-blocking finding — see below.** Created two real throwaway Outlook
Tasks sharing an identical SHORT subject ("AC07 Verify Dup Subject",
24 chars). Ran the real, bounded capture: two DISTINCT notes were
created (`...89E10000.md`, `...89E20000.md`), each carrying its own
correct `outlook_entry_id`, neither overwritten. The entry-id-suffix
disambiguation mechanism this task/`T02` built is confirmed correct.
**Separately, while completing this same AC's own verification against
the REAL, unbounded scheduled capture (`T04`'s own `AC-04` app-start
run, 100 real items processed):** three genuinely distinct real Outlook
Tasks were found sharing one 72-character subject
("Re: Azerbaijan Engagement – Data Lake Opportunity & Core42
Participation"). `task_note_filename_stem` correctly built three
distinct 92-character stems (confirmed via `task_note_index.json`,
which correctly recorded all three separately), but the shared,
pre-existing, already-tracked `_slugify` 80-char truncation defect
(`BUG-011`/`ESC-027`) collapsed all three onto one identical 80-char
filename — since Task notes share one flat `Work/Tasks/` subfolder (no
`kind` split), this caused a literal file OVERWRITE (only the last
write survives), a worse consequence than `BUG-011`'s own documented
Email/Notification case (different kind-subfolders, no literal
overwrite). Root-caused entirely to the pre-existing, out-of-scope
`_slugify` function (unmodified by `T02`, additive-only per its own
Constraints) — not a defect in this task's own new code, confirmed by
the passing short-subject control case above and by real production
data staying under the 80-char budget elsewhere (three distinct real
"ADNOC Account Plan Review..." tasks, 57 chars, correctly produced
three distinct files). Logged honestly, not silently worked around —
`ESCALATIONS.md` → `ESC-028`, `REVIEW-QUEUE.md` pointer added,
recommending `BUG-011`'s own `BUGS.md` entry be extended (same root
cause, worse severity finding), mirroring `ESC-027`'s own established
"a real, out-of-scope, root-caused defect discovered via due-diligence
live verification does not block the task that found it" precedent.

All throwaway Outlook Tasks and their notes/index entries cleaned up
after each check; the 25 (later 82, after `T04`'s own live capture)
real production Task notes were kept, per this project's own "real data
is fine to keep" precedent.

`gate: clear` 2026-08-13 — no MUST-FLAG trigger beyond the already-
disclosed, non-blocking `ESC-028` finding (which follows established
precedent, not a new pattern requiring a flag of its own beyond the
REVIEW-QUEUE pointer already added).

**Call-order reminder, unlike Meeting:** Task notes link no Person/
attendee at all (the story's own Constraints) — there is only ever one
possible body-line insert (`**Customer:**`), so there is no Attendees-
vs-Customer ordering question the way `meeting_classification.py`'s own
docstring has to explain.

**Why this module never gates on a `processed_task_ids.json`-style skip
check:** matches `meeting_classification.py`'s own established design
note — Scenario 2/6 both describe an already-captured task still flowing
through the top-up path on rerun, not being hard-skipped. The actual
no-duplicate guarantee comes from `vault_writer.lookup_task_note_stem`'s
own index-based create-vs-top-up branch, not from ID-based skipping.
