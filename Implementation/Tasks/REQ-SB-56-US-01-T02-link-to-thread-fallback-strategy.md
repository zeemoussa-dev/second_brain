---
id: REQ-SB-56-US-01-T02
title: Link-to-Thread Job — attendee-overlap + date-proximity fallback strategy (config-backed thresholds)
parent_story: REQ-SB-56-US-01
requirement_id: REQ-SB-56
type: backend
status: Done
gate: clear
gate_reason: "Built and verified 2026-08-17. No new MUST-FLAG trigger fired: no material assumption beyond one logged scope-internal judgement call (list_thread_notes() composes the existing list_notes_in_kind_folder(\"Threads\") rather than duplicating its glob mechanism); no ADR touched; no ESCALATIONS.md entry needed; every locked AC (AC-02 through AC-05) plus the config-not-hardcoded requirement verified via real code against a VAULT_PATH-scratch vault (see ## Implementation Log). This is the last task in REQ-SB-56-US-01 — story, SPRINT-053, and BACKLOG.md's REQ-SB-56 row all marked Done by this pass. SPRINT-053's own gate stays flagged — the story-level provisional-resolution spot-check on ESC-040 (T01's own scope) remains independently open in REVIEW-QUEUE.md, unaffected by and not blocking this task's own completion."
phase: P1
depends_on: [REQ-SB-56-US-01-T01]
created: 2026-08-17
updated: 2026-08-17
---

# REQ-SB-56-US-01-T02 — `Link-to-Thread` Job: attendee-overlap + date-proximity fallback strategy

## Parent Story

- Story: [[REQ-SB-56-US-01]] — `../UserStories/REQ-SB-56-US-01-meeting-capture-and-thread-linking.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-56 *Meeting Capture & Thread Linking*

---

## Objective

Add the fallback attendee-overlap + date-range-proximity linking strategy to the `Link-to-Thread` Job, for meetings the primary strategy structurally can't match (no shared `conversation_id`) — using REAL, **config-backed** threshold values (never hardcoded Python constants), and re-confirm `BACKLOG.md`'s `REQ-SB-53` row already marks `REQ-SB-53-US-02` superseded (Scenario 5).

---

## Starting State → End State

**Before / Inputs:**
- `T01`'s primary-strategy function/call site exists in `meeting_classification.py`.
- Thread notes already carry `participants` (list of sender emails, accumulated, never pruned) and `last_message_at` (ISO-8601 string, overwritten on every update) — written by `REQ-SB-55-US-01-T03`'s own `thread_match_merge` Job, already `Done` and shipped (`email_classification.py`). This task only READS them, never originates them — per the architecture's own ownership resolution ("`REQ-SB-56`'s own `Link-to-Thread` Job task reads them, it does not originate them").
- `outlook_com._resolve_attendees` / the event's own `"attendees"` list — `{"name","email"}` pairs, organizer/resource types already excluded.
- No existing `vault_writer.py` primitive enumerates every Thread note specifically — `list_all_note_paths()` lists everything vault-wide; a scoped Threads-only enumeration does not exist yet.
- **No existing config surface holds the attendee-overlap floor / 1:1 carve-out / date-proximity window.** These must NOT be Python constants inside `meeting_classification.py` — explicit operator instruction, 2026-08-17. They must be real, accessible config values, following this codebase's own established sibling-store/settings convention (`app/business/agent_prompts.py` + `.second-brain/agent_prompts.json`; `app/business/working_mode_registry.py`'s own self-healing seeded-default `_load_state()` shape — the closer precedent here, since this config is a single flat record, not per-id).

**After / Outputs:**
- **New config module `src/backend/app/business/meeting_thread_link_config.py`** (composed alongside `meeting_classification.py`, never inside it — mirrors `agent_prompts.py`/`working_mode_registry.py`'s own "compose alongside, don't bake into the consuming module" precedent, `ADR-011` point 2's "agent identity/type/actions stay hardcoded" reasoning applied here to keep threshold *values* out of the *linking logic* module too), backed by a **new sibling `.second-brain/meeting_thread_link_config.json`** store, self-healing to the operator-confirmed defaults on first read (mirrors `working_mode_registry._load_state()`'s own seeded-default pattern):
  - `attendee_overlap_floor` — default `2`
  - `one_on_one_carve_out_enabled` — default `true` (the "exactly 1 shared attendee that is the entirety of the smaller set" rule)
  - `date_proximity_days` — default `7`
  - Exposes `get_attendee_overlap_floor()`, `get_one_on_one_carve_out_enabled()`, `get_date_proximity_days()`, and matching `set_*` functions — programmatically settable (config-backed, tunable without a code change) even though nothing in this task wires them to HTTP/UI yet (see `## Out of Scope`).
- Two new `vault_writer.py` pure-I/O primitives: `load_meeting_thread_link_config()` / `save_meeting_thread_link_config(config)` — mirror `load_agent_prompt_record` / `save_agent_prompt_record`'s own shape (whole-record read/write, no defaulting logic in `vault_writer.py` itself, per `ADR-003` — defaulting belongs in the business layer).
- One new `vault_writer.py` enumeration primitive: `list_thread_notes() -> list[Path]` — a small, scoped Threads-folder enumeration mirroring `list_known_customers()`'s own frontmatter-scan shape.
- A new fallback-strategy function in `meeting_classification.py` (e.g. `_link_to_thread_by_fallback_heuristic(event, self_excluded_attendees) -> str | None`), called ONLY when `T01`'s primary strategy did not link (no `conversation_id`, or no matching Thread). For each candidate Thread (via `vault_writer.list_thread_notes()`):
  - self-excludes `settings.self_email` from BOTH the meeting's own attendee set and the Thread's own `participants` (mirrors `_exclude_self` exactly, applied to a plain email-string list on the Thread side).
  - computes the attendee-overlap count and applies BOTH clauses of the bar: `>= get_attendee_overlap_floor()` shared attendees, OR exactly 1 shared attendee that is the entirety of the smaller of the two sets, when `get_one_on_one_carve_out_enabled()` is true.
  - computes the date-range-proximity gap between the meeting's own `start` and the Thread's own `last_message_at`, against `get_date_proximity_days()` (inclusive, either direction).
  - requires BOTH bars to clear (AND) for a candidate to qualify.
  - tie-breaks multiple qualifying candidates: higher overlap count wins; if tied, smaller date gap wins; if still tied on both, no link (Scenario 3).
  - a Thread note missing either `participants` or `last_message_at` entirely is skipped outright (not treated as a zero-overlap non-match that could still win a tie).
  - returns the winning Thread's own `conversation_id`, or `None` if no candidate qualifies or a tie survives both tie-breaks.
- `classify_recent_meetings` calls the fallback only when `T01`'s primary strategy did not link, writing the returned `conversation_id` (if any) into the Meeting note's own `thread` field via the SAME `vault_writer.upsert_frontmatter_key` primitive `T01` uses — never a second write path.
- A meeting that clears neither strategy is left with `thread` at its reserved empty string — explicitly unlinked (Scenario 3), never a forced weak match.
- `BACKLOG.md`'s `REQ-SB-53` row is re-confirmed to already read "superseded"/"Parked" for `REQ-SB-53-US-02` (it does, as of this pass — see `## Context / Notes`) — no edit expected unless this task's own final check finds the row has regressed.

---

## Files to Modify

- `src/backend/app/business/meeting_thread_link_config.py` — **NEW file.** Config get/set surface, self-healing defaults.
- `src/backend/app/data_access/vault_writer.py` — add `load_meeting_thread_link_config()` / `save_meeting_thread_link_config(config)` (pure I/O, mirrors `load_agent_prompt_record`/`save_agent_prompt_record`), and `list_thread_notes()` (scoped Threads-folder enumeration, mirrors `list_known_customers()`'s own shape).
- `src/backend/app/business/meeting_classification.py` — add the fallback-strategy function and its call site (after `T01`'s primary-strategy call, only if it didn't link).
- `BACKLOG.md` — re-confirm (edit only if actually regressed) the `REQ-SB-53` row's own superseded/Parked wording for `REQ-SB-53-US-02`.

---

## Constraints

- Inherits from parent story: **false-positive links are worse than no link** — both bars are required (AND); any tie surviving both tie-breaks leaves the meeting unlinked, never forced to the closest weak match (Scenario 3).
- **Config, not hardcoded constants** (explicit operator instruction, 2026-08-17). The attendee-overlap floor, the 1:1 carve-out toggle, and the date-proximity window MUST be read from `meeting_thread_link_config.py`'s own `get_*` functions on every call, never inlined as Python literals inside `meeting_classification.py` or anywhere else in this task's own code. A hardcoded `2` / `7` / `True` anywhere in the fallback's own comparison logic is a task-scope violation, not a stylistic nit — a coder finding this easier to hardcode must not take that shortcut.
- Self-exclude `settings.self_email` from BOTH sides of every attendee-overlap comparison, mirroring `_exclude_self` exactly — do not reuse `_exclude_self` itself if it expects a differently-shaped list (it expects `{"name","email"}` dicts); a small local equivalent applied to the Thread's own `participants` (plain email strings) is expected.
- Only Thread notes already carrying BOTH `participants` and `last_message_at` are eligible candidates — a Thread note missing either field (e.g. pre-`REQ-SB-55` legacy state, if any exists) is skipped outright, never treated as a zero-overlap non-match that could still win a proximity tie.
- Do not modify `thread_match_merge` / `email_classification.py` — `participants`/`last_message_at` are read-only inputs to this task.
- Must respect `api → business → data_access` layering (`ADR-003`).

---

## Tests

**Manual verification steps:**
1. **[REQ-SB-56-US-01-AC-02]** Against a throwaway scratch vault, create a Thread note with `participants=["a@x.com","b@x.com"]`, `last_message_at` 2 days before a synthetic meeting's own `start`. Construct a synthetic meeting event with 2 overlapping attendees (after self-exclusion) and no `conversation_id` match. Run the fallback function. Confirm it returns that Thread's own `conversation_id`, and confirm the resulting Meeting note's `thread` field is populated with it.
2. **[REQ-SB-56-US-01-AC-02]** 1:1 carve-out: create a Thread note with `participants=["a@x.com"]` (a single-person set) and a synthetic meeting with exactly 1 overlapping attendee that is the ENTIRE smaller set, within the date window. Confirm this ALSO qualifies and links — proving the carve-out fires, not just the raw `>=2` floor.
3. **[REQ-SB-56-US-01-AC-03]** Construct a case that clears the attendee-overlap bar but NOT the date-proximity bar (e.g. `last_message_at` 30 days before the meeting's own `start`) — confirm the fallback returns `None` and the Meeting note's `thread` field stays empty. Repeat for the inverse (proximity clears, overlap does not — e.g. exactly 1 shared attendee that is NOT the entirety of either side's set, against a >=2-sized Thread) — confirm the same empty-unlinked outcome.
4. **[REQ-SB-56-US-01-AC-03]** Construct two candidate Threads that BOTH qualify with an identical overlap count AND an identical date gap (a genuine tie on both axes) — confirm the fallback returns `None` (unlinked), never an arbitrary pick.
5. Config-not-hardcoded check: call `meeting_thread_link_config.set_attendee_overlap_floor(3)` (or equivalent) before re-running step 1's own scenario with only 2 overlapping attendees — confirm it NOW fails to link (proving the comparison actually reads the configured value, not a baked-in `2`). Reset to the default afterward. Also confirm `.second-brain/meeting_thread_link_config.json` exists on disk after first read/write, holding all 3 keys.
6. **[REQ-SB-56-US-01-AC-04]** Full regression pass (both `T01` and `T02` now landed): run `classify_recent_meetings` end-to-end against a synthetic event that matches NEITHER strategy — confirm `customer` derivation, attendee Person-note linking, customer hub linking, and Meeting note create/top-up all produce the exact same outputs they did before this story (compare against `T01`'s own partial regression baseline).
7. **[REQ-SB-56-US-01-AC-05]** Open `BACKLOG.md`, inspect the `REQ-SB-53` row — confirm `REQ-SB-53-US-02` reads as superseded/Parked (by `REQ-SB-55`/`REQ-SB-56`), not reworked. If it does not, correct the row's own wording as part of this task's own Files to Modify.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] **AC-02** (Scenario 2) — a directly-created meeting with genuine attendee-overlap + date-proximity links via the fallback
- [x] **AC-03** (Scenario 3) — a meeting that fails either bar (or ties on both after qualifying) is left explicitly unlinked, never force-linked
- [x] **AC-04** (Scenario 4) — full existing meeting-capture behavior unaffected, verified after both `T01` and `T02` land
- [x] **AC-05** (Scenario 5) — `BACKLOG.md`'s `REQ-SB-53` row correctly marks `REQ-SB-53-US-02` as superseded/Parked
- [x] Attendee-overlap floor / 1:1 carve-out / date-proximity window are all read from `meeting_thread_link_config.py`'s own config surface — zero hardcoded threshold literals in the comparison logic
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- **Any HTTP endpoint or Settings UI surface for editing these thresholds.** No locked AC in this story tests threshold-editing (see the parent story's own `## Non-Goals`). `meeting_thread_link_config.py`'s `set_*` functions exist and are real (config-backed, not hardcoded), but nothing wires them to `app/api/*_router.py` or the frontend Settings screen in this task. **This is a deliberate scope boundary, not an oversight** — flagged explicitly here so a human isn't surprised the values aren't yet editable from the UI. A natural follow-up story could wire them into Settings, mirroring `REQ-SB-66`'s own `agent_prompts` endpoint precedent (`ADR-044`), once there's a real need to tune them without hand-editing `.second-brain/meeting_thread_link_config.json` directly.
- The synthesis that reads a linked Meeting into a Project's own Glimpse — `REQ-SB-57`'s own scope.
- Rebuilding `meeting-capture` into a full Pipeline of Jobs — this story stays a narrower, additive Job extension (parent story's own Non-Goals).

---

## Context / Notes

Full reasoning + grounding: `Implementation/Architecture/architecture.md` → "Meeting → Thread Linking — ConversationID Primary Strategy, Attendee-Overlap/Date-Proximity Fallback" (bars, tie-break, ownership resolution). `REQ-SB-56-US-01`'s own "Architect pass" / "Operator confirmation" / "Additional standing constraint" `## Notes` sections carry the confirmed default values verbatim. Precedent for the config module shape: `app/business/agent_prompts.py` (per-id record store) and `app/business/working_mode_registry.py` (self-healing seeded-default `_load_state()` — the closer shape for this task's own flat, non-per-id config). `MEMORY.md`'s `[2026-08-16] REQ-SB-66-US-01-T01` entry documents the sibling-JSON-store convention this task extends a further time over.

`BACKLOG.md`'s `REQ-SB-53` row, confirmed at decomposer pass (2026-08-17): already reads "**Parked** — Email (US-01) and Meetings (US-02) superseded by `REQ-SB-55`/`REQ-SB-56` below" — Scenario 5/`AC-05` should pass on inspection alone; step 7 above is a re-confirmation, not an expected edit.

---

## Implementation Log

**Build, 2026-08-17.**

- `src/backend/app/business/meeting_thread_link_config.py` — **NEW file.**
  `_load_state()` reads `vault_writer.load_meeting_thread_link_config()`;
  if `None`, seeds the full `{"attendee_overlap_floor": 2,
  "one_on_one_carve_out_enabled": True, "date_proximity_days": 7}` record
  and persists it; if present but missing any key (future-proofing), that
  one key alone is seeded and persisted, mirroring
  `working_mode_registry._load_state()`'s own per-agent self-healing loop
  applied here to per-key self-healing instead. `get_attendee_overlap_floor`
  / `set_attendee_overlap_floor`, `get_one_on_one_carve_out_enabled` /
  `set_one_on_one_carve_out_enabled`, `get_date_proximity_days` /
  `set_date_proximity_days` all round-trip through `_load_state()` +
  `vault_writer.save_meeting_thread_link_config`. No HTTP/UI wiring added
  — out of this task's own scope, confirmed against `## Out of Scope`.
- `src/backend/app/data_access/vault_writer.py` — added
  `_MEETING_THREAD_LINK_CONFIG_FILE = "meeting_thread_link_config.json"`;
  `_meeting_thread_link_config_path()` / `load_meeting_thread_link_config()`
  / `save_meeting_thread_link_config(config)` (pure I/O, mirrors
  `load_working_modes_state`/`save_working_modes_state` exactly — no
  defaulting logic here, per `ADR-003`); `list_thread_notes() -> list[Path]`.
  **Scope-internal judgement call (logged per Pipeline.md rule 5):**
  `list_thread_notes()` composes the already-existing
  `list_notes_in_kind_folder("Threads")` rather than duplicating its glob
  mechanism — the task's own Starting State said "no existing primitive
  enumerates every Thread note specifically," which is true of a
  *dedicated, discoverably-named* primitive, but `list_notes_in_kind_folder`
  already provides the identical scoped-folder-enumeration mechanism
  generically. Composing it (rather than re-implementing `Work/Threads/
  *.md` globbing a second time) satisfies the task's own literal
  requirement (a new, real `list_thread_notes()` primitive exists) without
  duplicating logic — no existing function, test, or caller was touched.
  No other line in `vault_writer.py` was modified.
- `src/backend/app/business/meeting_classification.py` — added
  `_exclude_self_from_participant_emails` (small local equivalent of
  `_exclude_self`, applied to a Thread's own plain email-string
  `participants` list, per this task's own Constraint — `_exclude_self`
  itself expects `{"name","email"}` dicts); `_date_proximity_gap_days`
  (absolute day-count gap via `datetime.strptime` on the leading
  `YYYY-MM-DD` prefix of each side — logged as a new `MEMORY.md` Pattern,
  since this codebase's own established default for date comparisons is
  string-prefix window-boundary compare, not `strptime`/`fromisoformat`;
  a real tie-break gap magnitude genuinely needs arithmetic a boundary
  compare can't give); `_attendee_overlap_bar_clears` (both clauses of
  the overlap bar, reading `meeting_thread_link_config.get_*` fresh on
  every call); `_link_to_thread_by_fallback_heuristic(event,
  self_excluded_attendees) -> str | None` (scans
  `vault_writer.list_thread_notes()`, skips any Thread missing
  `participants` or `last_message_at` outright, requires both bars (AND),
  tie-breaks by higher overlap then smaller date gap, leaves `None` on an
  unresolved tie). `classify_recent_meetings` now calls the fallback
  additively, only when `T01`'s primary strategy's own `thread_linked` is
  `False`, writing the returned `conversation_id` via the SAME
  `vault_writer.upsert_frontmatter_key` call `T01` uses — no second write
  path. No existing line of `classify_recent_meetings`,
  `_link_to_thread_by_conversation_id`, `_exclude_self`, or
  `_derive_meeting_customer` was changed.
- `BACKLOG.md` — `REQ-SB-53` row inspected: already reads "**Parked** —
  Email (US-01) and Meetings (US-02) superseded by `REQ-SB-55`/`REQ-SB-56`
  below," exactly as the decomposer's own pass recorded. No edit made —
  confirmed not regressed.

**Verification (manual mode — no automated test runner exists yet, per
`## Tests`'s own `n/a — test tooling pending`).** All runs used a fresh,
`VAULT_PATH`-env-overridden throwaway scratch vault
(`src/backend/.scratch/t02_scratch_vault`, deleted after this session — the
real vault was never touched) via a one-off verification script
(`src/backend/.scratch/t02_verify.py`, also deleted after use — not part of
this task's own `## Files to Modify`) that monkeypatches
`outlook_com.list_calendar_events` per scenario and runs the real,
unmodified `classify_recent_meetings` end-to-end, then reads back the
resulting Meeting note's own `thread` frontmatter field.

- **[REQ-SB-56-US-01-AC-02] / Test step 1 — PASS.** Thread
  `T02-TEST1-OVERLAP2` (`participants=["alice@buyer.com","bob@buyer.com"]`,
  `last_message_at="2026-08-15T09:00:00"`), synthetic meeting
  `start="2026-08-17 10:00:00+00:00"` with both attendees, no
  `conversation_id`. Observed: `thread_linked=True`, Meeting note's
  `thread` field read back as exactly `"T02-TEST1-OVERLAP2"` (2 shared
  attendees clears the floor; 2-day gap clears the 7-day window).
- **[REQ-SB-56-US-01-AC-02] / Test step 2 — PASS, 1:1 carve-out proven, not
  just the raw floor.** Thread `T02-TEST2-CARVEOUT`
  (`participants=["carol@oneone.com"]`, a single-person set), synthetic
  meeting with 2 attendees (`carol@oneone.com`, `dave@oneone.com`) — only
  1 overlaps, but it is the ENTIRETY of the Thread's own smaller
  1-person set. Observed: `thread_linked=True`, `thread` field read back
  as `"T02-TEST2-CARVEOUT"` — confirms the carve-out clause fires on its
  own (overlap count is 1, below the raw `>=2` floor).
- **[REQ-SB-56-US-01-AC-03] / Test step 3 — PASS, both directions.**
  (a) Thread `T02-TEST3A-FAROFF` (2 overlapping attendees, clears the
  overlap bar) with `last_message_at="2026-06-01T09:00:00"`, ~77 days
  from the meeting's own `start` — overlap clears but proximity fails.
  Observed: `thread_linked=False`, `thread` field stayed `""`.
  (b) Thread `T02-TEST3B-WEAKOVERLAP` (`participants=["gina@weak.com",
  "harry@weak.com"]`, a 2-person set) with `last_message_at` 1 day from
  the meeting's own `start` (clears proximity), against a synthetic
  meeting with 3 attendees where only `gina@weak.com` overlaps — overlap
  count 1, but NOT the entirety of either side's set
  (`min(3,2)=2 != 1`) — proximity clears but overlap fails. Observed:
  `thread_linked=False`, `thread` field stayed `""` — confirms the AND
  requirement in both directions, never a forced link on a lone-clearing
  bar.
- **[REQ-SB-56-US-01-AC-03] / Test step 4 — PASS.** Two candidate Threads
  (`T02-TEST4A-TIE`, `T02-TEST4B-TIE`), both `participants=["kim@tie.com",
  "leo@tie.com"]`, `last_message_at` 2 days before and 2 days after the
  meeting's own `start` respectively (identical overlap count = 2,
  identical date gap = 2, a genuine tie on BOTH axes). Observed:
  `thread_linked=False`, `thread` field stayed `""` — the tie-break
  correctly refuses to arbitrarily pick either candidate.
- **Config-not-hardcoded check — PASS.** `.second-brain/
  meeting_thread_link_config.json` confirmed present on disk after the
  first read/write, holding all 3 keys
  (`{"attendee_overlap_floor": 2, "one_on_one_carve_out_enabled": true,
  "date_proximity_days": 7}`). Called
  `meeting_thread_link_config.set_attendee_overlap_floor(3)`, then
  re-ran an otherwise-identical 2-overlap scenario (mirroring Test step
  1) — observed `thread_linked=False`, `thread` field stayed `""`,
  proving the comparison logic actually reads the configured value, not
  a baked-in `2`. Reset the floor back to its default (`2`) afterward and
  confirmed `get_attendee_overlap_floor() == 2` again.
- **[REQ-SB-56-US-01-AC-04] / Test step 6 — PASS, full regression
  (both `T01` and `T02` now landed).** Synthetic event matching NEITHER
  strategy (`conversation_id=""`, one attendee on an unrelated domain,
  no existing Thread's `participants` overlaps it). Observed:
  `created=True`, `customer=None`, `linked=False`, `attendees=1`,
  `thread_linked=False`, Meeting note's `thread` field stayed `""` — the
  exact same result-dict shape and values `T01`'s own partial regression
  pass established, now confirmed with `T02`'s fallback call site active
  too. No existing line of `classify_recent_meetings` or any of its
  existing helper functions produced a different output than before this
  story.
- **[REQ-SB-56-US-01-AC-05] / Test step 7 — PASS, re-confirmation only, no
  edit.** `BACKLOG.md`'s `REQ-SB-53` row read directly: "**Parked** —
  Email (US-01) and Meetings (US-02) superseded by `REQ-SB-55`/`REQ-SB-56`
  below." Matches the decomposer's own recorded expectation exactly — no
  regression found, no edit made.
- Confirmed by direct reading: `_link_to_thread_by_conversation_id`,
  `_exclude_self`, `_derive_meeting_customer`, `list_calendar_events`,
  `thread_note_path`/`thread_note_exists`/`create_thread_note_baseline`,
  and `email_classification.py::thread_match_merge` were not touched by
  this task.

**MEMORY.md / CHANGELOG.md:** both updated — see repo-root files. Two new
entries: a Decision recording this task's own build (the fourth real
sibling-JSON-store config module in this codebase), and a Pattern
recording the deliberate, narrow exception to this codebase's own
"avoid `datetime.fromisoformat`, string-slice instead" convention — a
real tie-break gap magnitude needs `datetime.strptime` on just the
leading date prefix, which is different from (and narrower than) a
wholesale reintroduction of full-timestamp parsing.

**Out of Scope confirmed untouched:** no HTTP endpoint or Settings UI
surface was wired for these thresholds (`meeting_thread_link_config.py`'s
`set_*` functions exist and are real, but nothing calls them from
`app/api/*_router.py` or the frontend); the Project Glimpse synthesis
that reads a linked Meeting (`REQ-SB-57`); rebuilding `meeting-capture`
into a full Pipeline of Jobs.

**Story/Sprint/BACKLOG propagation:** this was the last task in
`REQ-SB-56-US-01` (`T00`→`T01`→`T02`, all now `Done`) and the only story
in `SPRINT-053`. Story marked `status: Done`; `BACKLOG.md`'s `REQ-SB-56`
row updated to `Done`; `SPRINT-053` marked `status: Done`,
`completed: "2026-08-17"`, `## Retrospective` drafted (human harvest of
`Implementation/Learnings.md` still pending, per the standing
human-only-harvest rule). `SPRINT-053`'s own `gate` stays `flagged` — the
story-level provisional-resolution spot-check on `ESC-040` (whether the
operator's overnight Option (a) call was right, vs. investigating Option
(b) later) remains independently open in `REVIEW-QUEUE.md`, unaffected by
and not blocking this task's own completion; the retro captures this
honestly rather than silently closing it.

gate: clear 2026-08-17 — no coder-owned MUST-FLAG trigger fired on this
pass. No new material assumption beyond the one scope-internal judgement
call logged above (composing `list_notes_in_kind_folder` rather than
duplicating its glob mechanism inside `list_thread_notes()`); no ADR
touched; no `ESCALATIONS.md` entry needed (nothing new out-of-scope); every
locked AC (`AC-02` through `AC-05`) plus the config-not-hardcoded
requirement verified via real code against a `VAULT_PATH`-scratch vault.
