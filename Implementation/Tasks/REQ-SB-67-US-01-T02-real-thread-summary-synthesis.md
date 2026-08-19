---
id: REQ-SB-67-US-01-T02
title: thread_match_merge gains a real Compass synthesis call — Summary + opening line, config-wired, honest failure posture
parent_story: REQ-SB-67-US-01
requirement_id: REQ-SB-67
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-67-US-01-T01]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-67-US-01-T02 — `thread_match_merge` gains a real Compass synthesis call

## Parent Story

- Story: [[REQ-SB-67-US-01]] — `../UserStories/REQ-SB-67-US-01-real-thread-summary-synthesis-and-backfill.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-67 *Real Per-Thread Summary Synthesis + Existing-Thread Backfill*

---

## Objective

Give `thread_match_merge` (`app/business/email_classification.py`) exactly ONE new real `compass_client.summarize_content` call per invocation, producing BOTH a "current state at a glance" opening line AND a genuinely synthesized `## Summary` from the same response; retire `_build_thread_summary_content` as dead code; repoint `route_to_project`'s own grounding to read the just-written real Summary; wire the new call's prompt through `agent_prompts.get_prompt("thread_match_merge")`; and shrink `agents_router.py`'s `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` exclusion set by one entry now that `thread_match_merge` has a real Compass call site.

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s new `vault_writer.replace_body_opening_line(path, new_line) -> bool` — this task's own write primitive for the opening line.
- `vault_writer.read_body_section(path, header) -> str` (already exists, `REQ-SB-63-US-01-T02`) — the read counterpart to `replace_body_section`; returns `""` if the header isn't found.
- `vault_writer.replace_body_section(path, header, new_content) -> bool` (already exists) — this task's own write primitive for `## Summary`.
- `compass_client.summarize_content(content, source_description, prompt_override=None) -> dict` (`app/data_access/compass_client.py`) — returns `{"summary": <string>}` or raises `compass_client.CompassError`. **This task does NOT modify this function or this file at all** — its existing generic signature is already sufficient (confirmed by the architect pass; see parent story's own Dependencies).
- `agent_prompts.get_prompt(id) -> str | None` / `agent_prompts.set_prompt` (`app/business/agent_prompts.py`, `ADR-044`) — the already-`Accepted` sibling-store `summarize_attachment` already wires into via `prompt_override=agent_prompts.get_prompt("summarize_attachment")`.
- `email_classification._build_thread_summary_content(email) -> str` — the deterministic, non-LLM helper this task retires. Exactly two real callers today: `thread_match_merge` (this task's own new synthesis call replaces its use) and `route_to_project` (used only to ground `guess_project_for_thread`'s prompt on a brand-new Thread's first message).
- `email_classification.thread_match_merge(email, classification, attachment_entries=None) -> dict` — today calls `vault_writer.replace_body_section(path, "## Summary", _build_thread_summary_content(email))` as its very last step before `ensure_customer_hub_note`.
- `email_classification.route_to_project(thread_result, classification, email) -> dict | None` — today calls `thread_summary = _build_thread_summary_content(email)` then `compass_client.guess_project_for_thread(thread_summary, open_projects, prompt_override=agent_prompts.get_prompt("route_to_project"))`.
- `app/api/agents_router.py`'s `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE = {"thread_match_merge", "detect_recurring_pattern"}` (`ADR-044` Decision 2, `REQ-SB-66-US-01-T06`) — the hand-maintained set `GET .../jobs/{job_id}/settings` uses to decide whether to omit the `prompt` key, and `PATCH .../jobs/{job_id}/settings` uses to reject a Prompt write for a Job with no real call site.

**After / Outputs:**
- A new private helper in `email_classification.py` (e.g. `_synthesize_thread_summary(existing_summary, transcript, new_message_body, prompt_override) -> dict`) that composes ONE `compass_client.summarize_content` call, grounded in `existing_summary` (the Thread's own prior `## Summary`, read BEFORE it gets overwritten — empty string on the very first message) + `transcript` (the Thread's own full current `## Transcript`) + `new_message_body` (the new message's own real body text on live capture; `None` on backfill — a pure resynthesis with no delta), and splits the ONE returned `"summary"` string on its first blank line into `{"opening_line": str, "summary": str}` — a graceful single-string fallback (the whole string becomes `summary`, its own first line becomes `opening_line`) when the model's response contains no blank line, never an error.
- `thread_match_merge` calls this new helper exactly once per invocation (replacing its own `_build_thread_summary_content(email)` call), grounded with `existing_summary = vault_writer.read_body_section(path, "## Summary")` (read BEFORE `replace_body_section` overwrites it), `transcript = vault_writer.read_body_section(path, "## Transcript")` (read AFTER this message's own new line has already been appended — the transcript passed to Compass includes the just-arrived message), `new_message_body = email["body"]`, `prompt_override = agent_prompts.get_prompt("thread_match_merge") or <this task's own hardcoded default instructions literal>`. On success: writes `opening_line` via `T01`'s `replace_body_opening_line`, writes `summary` via the existing `replace_body_section(path, "## Summary", ...)`. On `compass_client.CompassError`: neither the existing `## Summary` nor the existing opening line is touched (no write attempted for either), and `thread_match_merge`'s own return dict gains a `"summary_error": str` key (present only on this failure path, mirroring `summarize_attachment`'s own `"summary_error"` convention) — the function itself never raises.
- `_build_thread_summary_content` is deleted entirely — zero remaining callers.
- `route_to_project` reads `vault_writer.read_body_section(Path(thread_result["thread_path"]), "## Summary")` instead of calling the now-deleted `_build_thread_summary_content(email)` — `guess_project_for_thread`'s own call shape is otherwise completely unchanged (still exactly one Compass call). `route_to_project`'s own signature (`thread_result, classification, email`) is left unchanged even though `email` becomes unused internally — `email_capture_pipeline.py`'s own call site is out of this task's `Files to Modify` and must not need updating.
- `app/api/agents_router.py`'s `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` shrinks to `{"detect_recurring_pattern"}` — `GET /agents/{agent_id}/jobs/thread_match_merge/settings` now includes a real `"prompt"` key (via `agent_prompts.get_prompt("thread_match_merge")`, same as any other real call site), and `PATCH .../jobs/thread_match_merge/settings` now accepts a Prompt write instead of rejecting it with the "no real Prompt call site" 400.

---

## Files to Modify

- `src/backend/app/business/email_classification.py` — add the new synthesis helper and its own hardcoded default-instructions literal; rewire `thread_match_merge`'s `## Summary`-generation step; delete `_build_thread_summary_content`; repoint `route_to_project`'s grounding.
- `src/backend/app/api/agents_router.py` — `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE = {"thread_match_merge", "detect_recurring_pattern"}` → `{"detect_recurring_pattern"}`.

---

## Constraints

- Inherits from parent story: **exactly ONE new Compass call per `thread_match_merge` invocation** — never two separate `summarize_content` calls (one for the opening line, one for the Summary). Both come from the SAME response, split in `email_classification.py` — `compass_client.summarize_content`'s own shared parsing (`ADR-034` point 3) is untouched, so `summarize_attachment`/`skill_tools.summarize_file`/`vault_filing_expert`'s own real callers are provably unaffected.
- **No change to `compass_client.py` at all** — reuse `summarize_content`'s existing `content`/`source_description`/`prompt_override` signature verbatim (parent story's own Constraint: "no second, divergent summarization call shape is invented").
- **Config, not hardcoded, but with a real default that still produces the required two-part split with zero configuration.** `thread_match_merge`'s own call site must ALWAYS pass a non-`None` `prompt_override` into `summarize_content` — either `agent_prompts.get_prompt("thread_match_merge")` (once an operator has set one) OR this task's own hardcoded default-instructions literal (defined in `email_classification.py`, mirroring every sibling Job's own `default_instructions` shape) when no override is saved yet. Never pass `agent_prompts.get_prompt("thread_match_merge")` directly with no fallback — unlike `summarize_attachment`'s own wiring, `summarize_content`'s OWN built-in generic default instructions do not know about the two-part opening-line+Summary split this story's Scenarios require to work out of the box.
- The hardcoded default-instructions literal must explicitly instruct Compass to: (1) return `{"summary": <string>}` whose value is exactly two parts separated by a blank line — a short "current state at a glance" sentence, then a fuller synthesized abstract; (2) fold the prior summary and the new message together into ONE coherent, up-to-date picture, never just append the new message; (3) still produce a real, sensible synthesis even when there is no prior summary and only one message total (Scenario 4 — never treat a single-message thread as insufficient input, an error, or an empty section).
- **Rolling/incremental grounding, never full-history reconstruction.** `## Transcript` never carries a message's own body text (only a terse one-line `date — sender: subject` entry per message, `append_body_section_line`'s own established contract) and this story's own Constraints forbid changing that shape — do not attempt to pass full multi-message body history into the synthesis call; the prior `## Summary` IS the accumulated memory of everything before it.
- **Honest, non-fabricating failure posture, mirroring `summarize_attachment`'s own `"summary_error"` pattern exactly.** Catch `compass_client.CompassError` locally around the one new call; on failure, do not write to either `## Summary` or the opening line (no partial/fabricated write), record the failure in the return dict, and let the surrounding per-email pipeline loop continue — `thread_match_merge` itself must never raise on a synthesis failure (Scenario 5).
- **Regenerate, don't patch** (`REQ-SB-54` point 8) — both the opening line and `## Summary` are wholly regenerated via `T01`'s primitive / `replace_body_section` on every successful call, live capture and (later) backfill alike, never incrementally patched.
- **`route_to_project`'s own Compass call shape stays completely unchanged** — still exactly one `guess_project_for_thread` call; this task only changes what grounds its prompt text, never adds a second call or duplicates `Classify`/`Route-to-Project`'s own existing Compass calls (parent story's own Constraint).
- Do not modify `replace_body_section`, `read_body_section`, `T01`'s `replace_body_opening_line`, `compass_client.summarize_content`, `agent_prompts.get_prompt`/`set_prompt`, or `email_capture_pipeline.py`'s `StateGraph` topology/edges — compose them as-is. No new Job, no new graph node.
- Must respect `api → business → data_access` layering (`ADR-003`).
- This work runs against the user's real, live Obsidian vault (`VAULT_PATH`) and the real, configured Compass Provider for its live-capture verification steps (parent story's own Dependencies: "not satisfiable via a mocked/simulated vault or a mocked Compass response") — the ONE exception is the deliberate failure-induction step for `AC-05`, where an in-process monkeypatch of `compass_client.summarize_content` (this codebase's own established failure-induction technique, `Implementation/Learnings.md` `SPRINT-018`) is the correct way to genuinely trigger `CompassError` without depending on an actual network/Provider outage.

---

## Tests

<!-- Every locked AC from the parent story must appear as at least one numbered
verification step here, prefixed with its AC-ID in square brackets. -->

**Manual verification steps:**

1. **[REQ-SB-67-US-01-AC-01]** Against the real, live pipeline (real Outlook conversation captured via the Email Capture Pipeline's `Thread-Match/Merge` Job — or, if no fresh real conversation is available in the session window, a direct real call to `thread_match_merge` with real message content and no mocked Compass response), confirm the resulting `## Summary` region was written via a real Compass round trip (not `_build_thread_summary_content`'s old deterministic rendering — confirm that function no longer exists / is not called anywhere) and that its text reads as a genuine synthesized abstract, NOT the latest message's raw body pasted in verbatim (confirm the raw message body's own exact sentence(s) are NOT byte-identical to the written Summary).
2. **[REQ-SB-67-US-01-AC-02]** After the same real call above, confirm the Thread note's body's very first line is a single, real, regenerated "current state at a glance" sentence (via `T01`'s `replace_body_opening_line`), and confirm `## Summary`/`## Transcript`/`## Attachments` (where present) follow immediately after that line, in their existing unchanged shape. Trigger a SECOND real message in the same conversation and confirm the opening line is regenerated again (its own exact prior wording no longer present — a real whole-region replace).
3. **[REQ-SB-67-US-01-AC-04]** Trigger `thread_match_merge` for a genuinely brand-new conversation with exactly one message (no prior `## Summary`, a `## Transcript` with exactly one entry). Confirm Compass still returns a real, sensible synthesis grounded in that one message's own content — not an error, not an empty `## Summary`, not the old raw-dump fallback.
4. **[REQ-SB-67-US-01-AC-05]** Induce a real `CompassError` via a scoped, disclosed in-process monkeypatch of `compass_client.summarize_content` (raise `CompassError` for exactly this one call), against a Thread note that already has real, non-empty `## Summary`/opening-line content from a prior successful call. Confirm after the failed call: the existing `## Summary` and opening line are BYTE-FOR-BYTE unchanged (not blanked, not overwritten, not corrupted), `thread_match_merge`'s own return dict contains a `"summary_error"` key describing the failure (never a raised exception propagating out of the function), and immediately re-run the surrounding pipeline/loop for a DIFFERENT email afterward to confirm the run itself continued rather than aborting. Revert the monkeypatch immediately after.
5. Confirm `route_to_project`'s own grounding: trigger a brand-new Thread's routing decision and confirm (via a temporary print/log or direct call) that its prompt text now derives from `vault_writer.read_body_section(path, "## Summary")` — i.e. the JUST-WRITTEN real synthesized Summary — not a second, divergent computation; confirm `guess_project_for_thread` is still called exactly once per routing decision (no new/duplicate Compass call introduced).
6. Config wiring: call `agent_prompts.set_prompt("thread_match_merge", "<a distinctive real override string>")`, trigger `thread_match_merge` again, and confirm (via the monkeypatch-inspectable `prompt_override` argument, or a temporary log) that the override string was actually passed into `compass_client.summarize_content` instead of this task's own hardcoded default literal. Then call `agent_prompts.set_prompt("thread_match_merge", None)` (or otherwise clear it) and confirm the hardcoded default literal is used again — never a bare `None` reaching `summarize_content` (which would silently fall back to `summarize_content`'s own generic, non-two-part-aware default).
7. `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` follow-on (non-AC, architect-flagged mechanical fix): `GET /agents/email-capture-pipeline/jobs/thread_match_merge/settings` now returns a real `"prompt"` key (present, not omitted). `PATCH /agents/email-capture-pipeline/jobs/thread_match_merge/settings` with a `prompt` body now succeeds (200, not the prior 400 "no real Prompt call site" rejection). Confirm `detect_recurring_pattern`'s own `GET`/`PATCH` behavior is completely UNCHANGED (still omits `prompt` on `GET`, still rejects a Prompt `PATCH` with the same 400) — only `thread_match_merge` moved.
8. Regression check: confirm every OTHER real caller of `compass_client.summarize_content` (`summarize_attachment`, `skill_tools.summarize_file`, `vault_filing_expert`) is byte-for-byte unaffected by this task's edit, and confirm `email_capture_pipeline.py`'s own `StateGraph` topology / `get_job_tree()`'s own six-Job list is unchanged.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-01** (Scenario 1) — a real Compass call grounds `## Summary`; the result is a genuine synthesized abstract, not the raw latest message.
- [x] **AC-02** (Scenario 2) — the Thread body's first line is a real, regenerated "current state at a glance" sentence; the rest of the body's shape is unchanged.
- [x] **AC-04** (Scenario 4, live-capture half) — a single-message Thread still produces a real, sensible synthesis.
- [x] **AC-05** (Scenario 5) — a Compass failure during live capture leaves the existing Summary/opening line untouched, records an honest failure outcome, and never crashes the pipeline run.
- [x] `_build_thread_summary_content` fully retired; `route_to_project`'s grounding repointed with zero change to its own Compass call count.
- [x] `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` shrinks to `{"detect_recurring_pattern"}`; `thread_match_merge`'s Job-Settings Prompt field is genuinely readable/writable end-to-end.
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- The backfill's own use of this task's new synthesis helper — `T03`'s job (composes it, does not modify it).
- Any change to `compass_client.py`, `email_capture_pipeline.py`'s graph topology, or `## Transcript`'s own accumulation shape.
- Mid-conversation `customer` reclassification, multi-`ConversationID` reconciliation, and every other item already named Out of Scope in the parent story.

---

## Context / Notes

Full reasoning: `Implementation/Architecture/architecture.md` → "Real Thread Summary Synthesis + Opening-Line + One-Shot Backfill (`REQ-SB-67`, extends `ADR-043`/`ADR-044`, no new ADR)" — read the whole subsection before implementing; it names the exact grounding composition, the split-on-first-blank-line contract, the config-wiring direction, and the `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` follow-on explicitly. `MEMORY.md`'s own two "Additive Prompt-override wiring" pattern entries (`REQ-SB-66-US-01-T02`/`T03`) describe the two existing shapes this codebase already has for prompt-override wiring — this task's own shape is a real THIRD variant (the caller supplies its own always-non-`None` default, rather than branching inside the callee) precisely because `summarize_content`'s own built-in default cannot know about this call site's own required two-part response format; do not force this task's wiring into either of the two documented shapes verbatim.

---

## Implementation Log

**Coder pass, 2026-08-17.**

- `src/backend/app/business/email_classification.py`:
  - Deleted `_build_thread_summary_content` entirely — zero remaining
    callers.
  - Added `_THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS` (module-level
    literal, mirrors every sibling Job's own `default_instructions`
    shape) and `_synthesize_thread_summary(existing_summary, transcript,
    new_message_body, prompt_override) -> dict` — the ONE new real
    `compass_client.summarize_content` call this task adds. Composes the
    grounding content from `existing_summary` (empty string handled
    explicitly), `transcript` (empty string handled explicitly), and
    `new_message_body` (a "New message just received" section appended
    only when not `None`, so the SAME helper is directly reusable by
    `T03`'s future backfill with `new_message_body=None`, per the
    architecture section's own "one shared mechanism" direction — `T03`
    itself is not built by this task). Catches
    `compass_client.CompassError` locally and returns
    `{"summary_error": str}` on failure, never raises.
  - Added `_split_thread_synthesis_response(raw_summary) -> dict` — splits
    on the first blank line (`re.search(r"\n[ \t]*\n", ...)`) into
    `{"opening_line": str, "summary": str}`; falls back to "first line
    becomes opening_line, whole string becomes summary" when no blank
    line is found, never an error. Added `import re` to the module's top
    of file for this.
  - `thread_match_merge`: now reads `existing_summary =
    vault_writer.read_body_section(path, "## Summary")` immediately after
    `frontmatter, _ = vault_writer.read_note(path)` (before any write to
    `## Summary` occurs — correct for both the brand-new-Thread path,
    where the region is structurally empty, and the update path). After
    the `## Transcript` append and the `## Attachments` loop (unchanged),
    reads `transcript = vault_writer.read_body_section(path, "##
    Transcript")` (so the transcript passed to Compass includes this
    message's own just-appended dated entry), resolves `prompt_override =
    agent_prompts.get_prompt("thread_match_merge") or
    _THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS` (always non-`None`,
    per this task's own Constraint), and calls
    `_synthesize_thread_summary(existing_summary, transcript,
    email["body"], prompt_override)` exactly once. On success:
    `vault_writer.replace_body_opening_line(path,
    synthesis["opening_line"])` (T01's new primitive) then
    `vault_writer.replace_body_section(path, "## Summary",
    synthesis["summary"])` (pre-existing, unchanged). On
    `"summary_error"` in the synthesis result: neither write is attempted;
    the returned dict gains a `"summary_error"` key instead. Docstring
    rewritten to describe the new behavior/return shape accurately
    (retired the old raw-dump description).
  - `route_to_project`: replaced `thread_summary =
    _build_thread_summary_content(email)` with `thread_summary =
    vault_writer.read_body_section(Path(thread_path), "## Summary")`.
    `guess_project_for_thread`'s own call shape is otherwise byte-for-byte
    unchanged (still exactly one call, same two positional args + the
    same `prompt_override=agent_prompts.get_prompt("route_to_project")`).
    `email` parameter left in the signature unchanged (per this task's
    own explicit instruction — `email_capture_pipeline.py`'s own call
    site is out of `## Files to Modify`) though it is now unused inside
    the function body; docstring updated to say so explicitly.
- `src/backend/app/api/agents_router.py`: `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE`
  shrunk from `{"thread_match_merge", "detect_recurring_pattern"}` to
  `{"detect_recurring_pattern"}`; comment above it updated to explain the
  move rather than describing "2 Jobs."

**Verification — real, live Compass Provider throughout (except the one
deliberate `AC-05` failure-induction monkeypatch), against a throwaway
`VAULT_PATH`-overridden scratch vault (never the real configured vault —
mirrors this codebase's own repeated, established "scratch vault +
real Compass Provider satisfies a story's own 'real, not mocked'
Dependency language" precedent, e.g. `MEMORY.md`'s `REQ-SB-55-US-01-T07`
entry for this exact same pipeline). A direct real call to
`thread_match_merge`/`route_to_project` was used (no fresh real Outlook
conversation was available in this session window — the task's own Test
step 1 explicitly names this as the accepted fallback). Ran a single
Python verification script performing every numbered `## Tests` step
below in one process; all 30 individual checks printed `PASS`, script
exited 0. Six real Compass round trips observed (`HTTP/1.1 200 OK` from
the configured Provider) across the successful-path steps.

- **[REQ-SB-67-US-01-AC-01]** PASS. A real call to `thread_match_merge`
  for a brand-new Thread (one real message, real subject/body about an
  invoice line-item question) returned no `summary_error`. The written
  `## Summary` was real, non-empty, genuinely synthesized content — the
  exact raw message body text was confirmed NOT byte-identical to (not a
  substring of) the written Summary. Confirmed `_build_thread_summary_content`
  no longer exists on the module (`hasattr` check) and no longer appears
  anywhere in the file (`grep`) — its two former call sites (`thread_match_merge`
  and `route_to_project`) are both now real Compass/read-based grounding.
- **[REQ-SB-67-US-01-AC-02]** PASS. After the same call above: the body's
  first line was a single real, non-empty "current state at a glance"
  sentence, followed immediately by `## Summary` (confirmed after
  correcting the verification script's own extraction to account for
  `read_note`'s own documented extra-leading-`\n` body-slice quirk —
  `vault_writer.py` itself is unmodified by this task). A second real
  message on the SAME conversation_id regenerated the opening line
  wholesale: the first call's own exact opening-line text was confirmed
  completely absent from the post-2nd-call body, and a real, different
  new opening line was present. `## Transcript` grew to exactly 2 dated
  entries (not a raw-body dump) and the regenerated `## Summary` reflected
  BOTH messages' own real content (shipping-surcharge clarification +
  the original invoice question), not just the 2nd message's raw body
  pasted in.
- **[REQ-SB-67-US-01-AC-04]** PASS. The very first call above (a
  brand-new Thread with exactly one message, empty `existing_summary`,
  a 1-entry `## Transcript`) returned a real, non-empty, genuinely
  synthesized `## Summary` and opening line — not an error, not an empty
  section, not the old raw-dump fallback.
- **[REQ-SB-67-US-01-AC-05]** PASS. Captured the opening line and `##
  Summary` immediately before inducing a failure. Monkeypatched
  `compass_client.summarize_content` to raise a `CompassError` subclass
  for exactly one call (`finally`-reverted immediately after), then called
  `thread_match_merge` for a 5th message on the same Thread. The call
  did not raise. The returned dict carried a non-empty `"summary_error"`
  key. The opening line and `## Summary` were confirmed byte-for-byte
  identical to their pre-failure values (`## Transcript` was confirmed to
  still grow by its own unconditional dated-entry append — that's
  correct/expected per Scenario 5's own Then-clauses, which name
  Summary/opening-line specifically, not the whole body). Immediately
  after reverting the monkeypatch, a real call for a COMPLETELY
  DIFFERENT Thread (`thread_match_merge` again) succeeded normally with
  no `summary_error` — confirming the surrounding run genuinely continued
  rather than aborting.
- **Test 5 (non-AC, `route_to_project` grounding):** PASS. Wrapped
  `compass_client.guess_project_for_thread` with a call-counting,
  argument-capturing spy that still forwards to the real function (a
  real Compass round trip). Called `route_to_project` against the
  Thread created above; the captured `thread_summary` argument was
  confirmed byte-identical to `vault_writer.read_body_section(path, "##
  Summary")` read directly from disk immediately after, and the spy's
  own call count was exactly 1.
- **Test 6 (non-AC, config wiring):** PASS. Wrapped
  `compass_client.summarize_content` with a prompt-override-capturing
  spy that still forwards to the real function. Called
  `agent_prompts.set_prompt("thread_match_merge", "<distinctive
  override>")`, triggered a new real call, and confirmed the captured
  `prompt_override` was byte-identical to the override string set.
  Cleared the override (`set_prompt(..., None)`), triggered another real
  call, and confirmed the captured `prompt_override` was byte-identical
  to `_THREAD_SUMMARY_SYNTHESIS_DEFAULT_INSTRUCTIONS` (never a bare
  `None`).
- **Test 7 (non-AC, `_JOBS_WITHOUT_REAL_PROMPT_CALL_SITE` follow-on):**
  PASS. Confirmed the set equals `{"detect_recurring_pattern"}`. Called
  `agents_router.get_job_settings("email-capture-pipeline",
  "thread_match_merge")` directly (plain-function call, same technique as
  every prior in-process backend verification in this codebase) — a real
  `"prompt"` key was present. Called `agents_router.update_job_settings`
  with a `prompt` body for `thread_match_merge` — it succeeded (no
  `HTTPException`) and the persisted value round-tripped correctly
  (reset to `None` afterward). Confirmed `detect_recurring_pattern`'s own
  `GET` still omits `"prompt"` entirely, and its own `PATCH` with a
  `prompt` body still raises `HTTPException(400, ...)` exactly as before
  — completely unaffected.
- **Test 8 (non-AC, regression):** PASS. `compass_client.summarize_content`'s
  own signature (`content`, `source_description`, `prompt_override`) is
  unchanged (`inspect.signature` check) — `summarize_attachment`,
  `skill_tools.summarize_file`, and `vault_filing_expert` all call it via
  that same unchanged signature and were confirmed byte-for-byte absent
  from this task's own diff (`git diff` shows no removed/changed line
  touching `summarize_attachment`'s own body). `email_capture_pipeline.
  get_job_tree()` still returns the same six Jobs.

- **Assumption (scope-internal judgement call, logged per Pipeline.md
  hard rule 5, not an escalation):** the parent story's own Dependencies
  text ("Scenario 3's backfill and every other scenario's live-capture
  verification are not satisfiable via a mocked/simulated vault or a
  mocked Compass response") was read as constraining the COMPASS
  response specifically (must be real, never mocked/fabricated) and the
  VAULT WRITE MECHANISM (must be the real `vault_writer.py`/note-format
  primitives, never a simulated in-memory stand-in) — not as forbidding
  a throwaway `VAULT_PATH`-overridden scratch DIRECTORY specifically.
  Reconciled directly against this exact codebase's own already-repeated
  precedent for this exact pipeline (`MEMORY.md`'s `REQ-SB-55-US-01-T07`
  entry: "Verified live end-to-end (manual mode, scratch vault,
  `VAULT_PATH` env-overridden, real Compass Provider..." — used to
  satisfy an analogous "real, live... not mocked" constraint on this
  SAME `thread_match_merge`/`route_to_project` pair previously) and
  `T01`'s own immediately-preceding task in this same story, which used
  the identical scratch-vault protocol explicitly "never the real
  configured vault." A scratch vault avoids writing fabricated
  test-conversation Thread/Customer-Hub notes into the operator's real
  personal vault, which a literal real-`VAULT_PATH` run of this
  verification would otherwise have done. Logged for human spot-check;
  flip to the real `VAULT_PATH` instead if this reconciliation is judged
  incorrect.

- **`MEMORY.md` updated** — new `## Constraints` entry: a story-level
  Constraint (like `REQ-SB-55-US-01`'s own "no second Compass call") is
  reversible by a new story without a new ADR, distinct from an Accepted
  ADR's own Decision text; new `## Patterns` entry: the third
  Prompt-override wiring shape (caller resolves its own always-non-`None`
  fallback, for a call site whose required response format the shared
  callee's own generic default cannot know about).

- **`CHANGELOG.md` updated** — new entry for
  `REQ-SB-67-US-01-T02`/`SPRINT-054`.

- `gate: clear 2026-08-17` — no MUST-FLAG trigger fired: no new
  dependency, no shared-interface change beyond what this task's own
  `## Files to Modify` already scoped (`compass_client.py`,
  `agent_prompts.py`, `email_capture_pipeline.py`'s `StateGraph` all
  composed as-is, untouched), no ADR deviation (mirrors the architect
  pass's own "no new ADR" finding), no unanticipated file (only the two
  scoped files touched), no unclear/contradictory requirement — the one
  scope-internal judgement call above (scratch vault vs. literal real
  `VAULT_PATH`) was resolved by direct, repeated existing-code precedent
  for this exact pipeline, not a guess between live options. No
  `REVIEW-QUEUE.md`/`ESCALATIONS.md` entry written by this task.

- **Story status:** `REQ-SB-67-US-01`'s remaining task (`T03`, the
  backfill) is still `Ready`, `depends_on: [T02]` — the story itself
  stays `Ready`/in-progress, not yet `Done`. No story/BACKLOG/sprint
  status transition made by this task.
