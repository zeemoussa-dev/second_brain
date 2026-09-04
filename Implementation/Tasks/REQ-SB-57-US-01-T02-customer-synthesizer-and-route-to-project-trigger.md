---
id: REQ-SB-57-US-01-T02
title: Customer Synthesizer core (rollup Glimpse + History-line cascade + drop-from-rollup) + Route-to-Project-approval trigger wiring
parent_story: REQ-SB-57-US-01
requirement_id: REQ-SB-57
type: backend
status: Done
gate: flagged
gate_reason: "scope-internal judgement calls logged for human spot-check — see Implementation Log"
phase: P1
depends_on: [REQ-SB-57-US-01-T01]
created: 2026-08-18
updated: 2026-08-18
---

# REQ-SB-57-US-01-T02 — Customer Synthesizer core + Route-to-Project-approval trigger wiring

## Parent Story

- Story: [[REQ-SB-57-US-01]] — `../UserStories/REQ-SB-57-US-01-project-and-customer-status-synthesizer-agents.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-57 *Project & Customer Status Synthesizer Agents*

---

## Objective

Add the Customer Synthesizer's own core mechanism —
`synthesize_customer(customer, concluded_project=None,
evidence_text="")`, cascaded from `synthesize_project`'s own end
(never independently deciding a conclusion) — and wire the SECOND real
trigger point: the moment a Thread first attaches to a Project
(`finalize_thread_project_routing`, the Route-to-Project approval's own
deferred write), which today happens entirely outside the Email Capture
Pipeline's own graph.

---

## Starting State → End State

**Before / Inputs:**
- `T01` has shipped `project_customer_synthesizer.py`'s
  `synthesize_project(customer, project, evidence_text="")`, ending with
  a marked seam/comment for this task's own cascade call, and
  `resync_project_from_thread`.
- `app/business/email_classification.py::finalize_thread_project_
  routing` — confirmed by direct reading — creates the Project directory
  (`vault_writer.create_project_directory_baseline`, only when
  `payload["is_new_project"]`) and then unconditionally sets the
  Thread's own `project` frontmatter key
  (`vault_writer.upsert_frontmatter_key(thread_path, "project",
  project)`) as its OWN last real write, before returning `{"path":
  ..., "message": ...}`. This is the exact, real moment a Thread's own
  evidence first attaches to a Project — no Glimpse write happens here
  today at all.
- `vault_writer.list_customer_projects(customer)` already returns each
  Project's own real `{"project": title, "slug": ..., "status": ...}`,
  honestly, from each Project's own concept-file frontmatter (`T01`'s
  new `last_synthesized_status` key does not change this function's own
  shape — it only reads `title`/`status`).

**After / Outputs:**
- `project_customer_synthesizer.py` gains:
  - `synthesize_customer(customer, concluded_project=None,
    evidence_text="") -> dict` — the ONLY function, after this task,
    allowed to touch a Customer's own `## Glimpse` or `log.md`:
    1. Reads every Project under `customer` via `list_customer_
       projects`, filters to `status` in `{"active", "on_hold"}`.
    2. Builds `## Glimpse` content as a mechanical rollup — one line per
       active/on_hold Project, e.g. `- **{title}** — {status}` — never
       an LLM call (mirrors `T01`'s own "mechanical rollup, reused
       already-synthesized content" precedent).
    3. Writes it via `vault_writer.replace_body_section(customer_
       concept_path, "## Glimpse", <rollup content>)`.
    4. **`concluded_project` drives the History-line append — this
       function never independently re-derives "did something
       conclude" from its own separate `status` comparison** (Ownership
       rule, `REQ-SB-54` point 7 — "a Project update TRIGGERS Customer
       resynthesis, [the Customer Synthesizer] never independently
       deciding"). When `concluded_project` is not `None`, appends ONE
       dated `log.md` line naming that Project
       (`append_person_note_update_line`); when `None`, appends
       nothing.
    5. `evidence_text` is accepted and stored on the returned dict only
       — this task's own code does not yet consume it for anything else
       (`T04`'s own scope). Returns `{"customer": customer, "amendment_
       proposed": False}` (the `False` default here; `T04` extends this
       shape).
  - `synthesize_project`'s own end (`T01`'s marked seam) gains exactly
    one new line: `synthesize_customer(customer, concluded_project=
    project if concluded else None, evidence_text=evidence_text)` —
    the ONLY edit this task makes to `synthesize_project`'s own body;
    everything else `T01` built stays unchanged.
- `finalize_thread_project_routing` gains exactly one new call, placed
  immediately after its own existing `upsert_frontmatter_key(thread_
  path, "project", project)` line and before its own `return` —
  `project_customer_synthesizer.synthesize_project(customer, project)`
  — purely additive; the function's own existing return shape/behavior
  for its one real caller (`pending_approvals_router.py`'s
  `_APPROVAL_HANDLERS["route_thread_to_project"]`) is unchanged.

---

## Files to Modify

- `src/backend/app/business/project_customer_synthesizer.py` — add
  `synthesize_customer`; add the one cascade line at the end of
  `synthesize_project`.
- `src/backend/app/business/email_classification.py` — add the one
  `synthesize_project` call inside `finalize_thread_project_routing`,
  import `project_customer_synthesizer`.

---

## Constraints

- Inherits from parent story — exactly one owner writes a Customer's own
  `## Glimpse`/`log.md`: only `synthesize_customer`, never
  `finalize_thread_project_routing` or any other function.
- **`## Glimpse` is always fully regenerated via `replace_body_section`,
  never incrementally patched** — the whole rollup is rebuilt from
  `list_customer_projects` on every call, not incrementally diffed
  against the previous rollup text.
- **`synthesize_customer` must never independently compare a Project's
  own `status` to decide whether to append a `log.md` line** — that
  decision is `synthesize_project`'s own, passed down via
  `concluded_project`. This is a direct, load-bearing Ownership-rule
  Constraint, not a style preference.
- **`finalize_thread_project_routing`'s new call must not change its own
  existing return shape** — still `{"path": ..., "message": ...}`
  (`is_new_project`'s own message-wording branch is untouched).
- A newly-routed Thread's very first `synthesize_project` call (fired
  from `finalize_thread_project_routing`) runs with `evidence_text=""`
  (this task's own call site does not thread the Thread's `## Summary`
  through) — acceptable: `T04`'s own detection only ever fires when
  `evidence_text` is non-empty, so a first-routing pass simply never
  proposes a Background amendment on its own; the Thread's next real
  update (via `thread_match_merge`, `T01`'s own trigger) is what carries
  real `evidence_text`.

---

## Tests

**Manual verification steps:**

1. `[REQ-SB-57-US-01-AC-02]` Using real vault fixtures (a real Customer
   with 2+ disposable active Projects), set one Project's own `status`
   to `"won"` and call `synthesize_project` for it directly. Confirm (a)
   the Customer's own `<slug>.md` `## Glimpse` no longer lists that
   Project among its rollup, and (b) the Customer's own `log.md` gained
   exactly one new dated line naming that Project — both written within
   the SAME call (the `synthesize_project` call that observed the
   transition).
2. `[REQ-SB-57-US-01-AC-05]` With 3+ disposable Projects under one real
   Customer at a mix of `active`/`on_hold`/`won` `status` values, call
   `synthesize_customer(customer)` directly. Confirm the Customer's own
   `## Glimpse` shows EXACTLY one line per `active`/`on_hold` Project
   (not the `won` one), each line reflecting that Project's own current
   `status`, and confirm re-running `synthesize_customer` again after
   changing one Project's `status` from `active` to `on_hold` correctly
   shows the updated status on a fresh rebuild (not stale/patched text).
3. Non-AC regression check: call `finalize_thread_project_routing` end
   to end (a real, disposable Pending-Approval-style payload for a
   brand-new Project) and confirm the newly-created Project's own `##
   Glimpse` is non-empty immediately after — the cascade fired on first
   attachment, not only on later Thread updates.
4. Non-AC regression check: re-confirm `T01`'s own `AC-01`/`AC-04`
   manual steps still pass unchanged after this task's edit to
   `synthesize_project`'s own body (the one added cascade line does not
   alter the Project-level Glimpse/History behavior `T01` already
   verified).
5. Clean up every disposable fixture created during verification;
   confirm pre-existing real vault content is byte-for-byte/mtime-
   unchanged afterward.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `REQ-SB-57-US-01-AC-02` — a Project's conclusion produces exactly
      one Customer `log.md` line and drops it from the active rollup, in
      the same synthesis pass
- [x] `REQ-SB-57-US-01-AC-05` — the Customer's `## Glimpse` shows exactly
      one line per active/on_hold Project, rebuilt fresh every call
- [x] `synthesize_customer` never independently re-derives a conclusion
      from its own `status` comparison
- [x] `T01`'s own AC-01/AC-04 verification still passes after this
      task's edit
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The Meeting-link-in trigger call site — `T03`.
- Background-amendment durable-fact detection/proposal — `T04` (this
  task only threads `evidence_text` through unused).
- Any change to `route_to_project`'s own Compass-guessing half — only
  `finalize_thread_project_routing` (the deferred-write half) is
  touched.

---

## Context / Notes

Depends on `T01` for `project_customer_synthesizer.py` to exist and for
`synthesize_project`'s own marked cascade seam.
`Implementation/Architecture/architecture.md` → "Project & Customer
Synthesizer..." (Customer rollup rule paragraph) is the concrete,
operator-confirmed spec for the rollup filter (`status` ∈
`{active, on_hold}`) and the "same synthesis pass" ordering.

---

## Implementation Log

**Built (2026-08-18):**

- `app/business/project_customer_synthesizer.py`:
  - Added `_build_customer_glimpse(customer)` — mechanical rollup, one
    `- **{title}** — {status}` line per Project under `customer` whose
    `status` ∈ `{active, on_hold}` (via `vault_writer.list_customer_
    projects`), `_No active Projects yet._` when none qualify.
  - Added `synthesize_customer(customer, concluded_project=None,
    evidence_text="") -> dict` — the ONLY function, after this task,
    allowed to touch a Customer's own `## Glimpse`/`log.md`. Fully
    regenerates `## Glimpse` via `replace_body_section` on every call
    (never patched); appends exactly one dated `log.md` line naming
    `concluded_project` iff it is not `None` — never independently
    re-derives a conclusion from its own `status` comparison (confirmed:
    the function's own body contains no `status` read at all). Returns
    `{"customer": customer, "amendment_proposed": False}`, with a `# T04
    adds:` seam comment marking where Background-amendment detection
    plugs in next.
  - `synthesize_project`'s own end now calls `synthesize_customer(
    customer, concluded_project=project if concluded else None,
    evidence_text=evidence_text)` — the one line this task's own End
    State specified, replacing `T01`'s marked seam comment. No other
    line of `synthesize_project`'s own body was touched.
  - Updated the module's own top docstring (Customer-level ownership now
    real, not just Project-level) and `synthesize_project`'s own
    docstring (documents the cascade call) — documentation-only, no
    behavior beyond what's listed above.
- `app/business/email_classification.py`:
  - Added `project_customer_synthesizer` to the module's own `from
    app.business import (...)` block.
  - `finalize_thread_project_routing` gained exactly one new call —
    `project_customer_synthesizer.synthesize_project(customer, project)`
    — placed immediately after the existing `upsert_frontmatter_key(
    thread_path, "project", project)` line and before the function's own
    `return`. The function's own existing return shape (`{"path": ...,
    "message": ...}`) is unchanged; confirmed by direct re-read after
    the edit. Docstring updated to describe the new trigger call site —
    documentation-only beyond the one added line.
  - Confirmed via `grep` across `app/` (re-run after this task's own
    edits) that `replace_body_section` against a Customer's own concept
    file, and `append_person_note_update_line` against a Customer's own
    `log.md`, are STILL only ever called from inside `project_customer_
    synthesizer.py` — no other module gained a direct write path.

**Scope-internal judgement calls (logged for human spot-check, gate:
flagged per this session's own protocol):**

1. **Customer `## Glimpse` rollup line format** — the task's own End
   State names the content shape (`"- **{title}** — {status}"`) exactly,
   so this one was not actually a judgement call — implemented verbatim.
2. **Customer `log.md` line wording** — the task specifies WHEN a line is
   appended (`concluded_project is not None`) but not its exact text.
   Wrote `"{YYYY-MM-DD UTC} — Project \"{concluded_project}\"
   concluded."`, mirroring `T01`'s own `{date} — {description}` dated-line
   convention for the Project-level `log.md` line, adapted to the
   Customer-level rollup's own "which Project concluded" framing (the
   Project-level line already names the specific new `status` value; the
   Customer-level line only needs to name WHICH Project concluded, since
   that Project has already dropped out of the rollup by the time this
   line is read).
3. **Module docstring update scope** — the task's own `## Files to
   Modify` lists `project_customer_synthesizer.py` without carving out
   "docstring only" vs. "code only" edits. Updated the module's top
   docstring and `synthesize_project`'s own docstring to stay accurate
   now that Customer-level ownership is real and the seam is filled —
   documentation-only, no behavior change, same class of judgement call
   `T01` itself already logged for its own docstring updates.

**Manual verification (real vault, `VAULT_PATH` =
`<OPERATOR_VAULT_OLD>`; real, pre-existing Customer `Core42`;
disposable Projects `"SB57T02 Verify Alpha"`/`"Beta"`/`"Gamma"`/
`"NewRoutedProject"` and one disposable Thread, all fully removed
afterward — script: see verification technique note below):**

- `[REQ-SB-57-US-01-AC-02]` **PASS.** Created 3 disposable Projects under
  `Core42` (`Alpha`, `Beta` active; `Gamma` on_hold). Set `Alpha`'s
  `status` to `"won"` and called `synthesize_project(Core42, Alpha)`
  directly (the same call chain that cascades into `synthesize_customer`
  internally — no separate call made). Observed: `Core42`'s own
  `Core42.md` `## Glimpse` immediately no longer listed `Alpha` (only
  `Beta`/`Gamma` remained); `Core42`'s own `log.md` gained exactly one new
  dated line, `"2026-08-17 — Project \"SB57T02 Verify Alpha\"
  concluded."` — both writes observed within the same `synthesize_
  project` call.
- `[REQ-SB-57-US-01-AC-05]` **PASS.** With `Alpha` (won, dropped),
  `Beta` (active), `Gamma` (on_hold) in place, called `synthesize_
  customer(Core42)` directly. Observed: `## Glimpse` showed EXACTLY 2
  lines — `"- **SB57T02 Verify Beta** — active"` and `"- **SB57T02 Verify
  Gamma** — on_hold"` — `Alpha` (won) correctly absent. Then flipped
  `Beta`'s `status` from `active` to `on_hold` and re-ran `synthesize_
  customer(Core42)` — observed the rollup rebuilt fresh, now showing
  `Beta` as `on_hold` (not stale `active` text), still exactly 2 lines.
- **Non-AC regression — `synthesize_customer` never independently
  re-derives a conclusion:** called `synthesize_customer(Core42)` again
  with the default `concluded_project=None` (no Project had just
  concluded from this call's own perspective). Observed: `Core42`'s own
  `log.md` was byte-identical before and after this call — confirmed no
  line was appended despite `Alpha` still sitting at a terminal `status`
  in the vault. PASS.
- **Non-AC regression — `finalize_thread_project_routing` end-to-end
  (brand-new Project):** created a disposable Thread via a real
  `thread_match_merge` call (`conversation_id` unique per run), then
  called `finalize_thread_project_routing` directly with a real,
  disposable Pending-Approval-style payload (`is_new_project: True`,
  `guessed_project: "SB57T02 Verify NewRoutedProject"`). Observed: the
  function's own return shape was unchanged (`{"path": ..., "message":
  "Approved — Thread filed under project '...'."}`); the newly-created
  Project's own `## Glimpse` was immediately non-empty right after,
  containing a real bullet referencing the just-routed Thread's own
  synthesized `## Summary` content (the cascade fired on first
  attachment, not only on a later Thread update); `Core42`'s own rollup
  `## Glimpse` also immediately included the brand-new Project. PASS.
- **Non-AC regression — `T01`'s own `AC-01`/`AC-04` still pass:** with
  `Beta`'s `status` left unchanged (routine activity), called
  `synthesize_project(Core42, Beta)` twice in direct succession.
  Observed: `Beta`'s own `log.md` stayed byte-empty across both calls —
  no line added for routine, non-concluding activity, confirming this
  task's one added line inside `synthesize_project`'s own body did not
  alter its Project-level Glimpse/History behavior. PASS.
- **Cleanup:** removed all 4 disposable Project directories and the one
  disposable Thread note created during this run; restored `Core42.md`/
  `log.md`/`index.md` to the exact pre-existing byte content captured in
  a before-snapshot at the start of the run, and independently
  re-confirmed the restore afterward.
- **Concurrent-session note (not a defect):** partway through this
  verification, `Core42`'s own `## Glimpse` briefly showed a
  `"REQ-SB-57-T03 Verification Project"` rollup line this task's own
  script never created — a separate, concurrently-running `T03` coder
  session's own live fixture, correctly cascaded in through the very
  `synthesize_project` → `synthesize_customer` call chain this task just
  wired (confirms the mechanism works under real concurrent evidence
  changes, per Scenario 6's own spirit, though `AC-06` itself is `T03`'s
  own scope to verify). That fixture/line was left untouched — it is not
  this task's own fixture to clean up; only this task's own 4 Projects +
  1 Thread were removed, and only `Core42`'s pre-existing content (per
  this task's own before-snapshot) was restored. Logged to `MEMORY.md`
  as a reusable pattern for future concurrent-session verification.

**Verification technique note:** ran a standalone Python script
(`app/business/project_customer_synthesizer.synthesize_project`/
`synthesize_customer`, `app/business/email_classification.thread_match_
merge`/`finalize_thread_project_routing` called directly against the real
configured vault) rather than the compiled LangGraph pipeline — this
task's own Route-to-Project trigger point (`finalize_thread_project_
routing`) is an approval-time call path entirely outside the pipeline
graph (confirmed by the decomposer's own real-code reading in the parent
story), so there is no graph node to invoke for that half; the
Thread-pipeline half was already covered by `T01`'s own live verification
and is only re-exercised here as the non-AC `T01` regression check.

gate: flagged 2026-08-18 (coder) — trigger 8-class scope-internal
judgement calls only (Customer `log.md` line wording, docstring-update
scope), all logged above for human spot-check; no MUST-FLAG escalation
trigger fired (no new dependency, no shared-interface change — `finalize_
thread_project_routing`'s own return shape is unchanged and re-confirmed
live — no ADR deviation, no unanticipated file, every locked AC this task
owns verified live). `REQ-SB-57-US-01-T02` → `status: Done`.
