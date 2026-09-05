---
id: REQ-SB-82-US-02-T02
title: research-kb-writer Skill + live research-agent Hermes profile provisioning
parent_story: REQ-SB-82-US-02
requirement_id: REQ-SB-82
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P2
depends_on: []
created: 2026-08-25
updated: 2026-08-25
---

# REQ-SB-82-US-02-T02 — research-kb-writer Skill + live research-agent Hermes profile provisioning

## Parent Story

- Story: [[REQ-SB-82-US-02]] — `../UserStories/REQ-SB-82-US-02-research-agent-librarian-section.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-82 *Cockpit Mechanics — Prep, Research, and Moderation*

---

## Objective

Author the `research-kb-writer` Skill (script + `SKILL.md`) that writes a
research finding as a brand-new, additive note into `Work/Research/`, then
provision the real, live `research-agent` Hermes profile (Librarian
Section, `web_search`/`terminal` tools, this Skill installed) needed to
prove this story's Scenarios end-to-end.

---

## Starting State → End State

**Before / Inputs:**
- No research/web-lookup mechanism exists anywhere in the current,
  post-Hermes-pivot codebase (confirmed, see story Context).
- `Hermes-Provisioning/skills/` has no `librarian/` category yet.

**After / Outputs:**
- `Hermes-Provisioning/skills/librarian/research-kb-writer/scripts/write_research_doc.py` — a CLI script: `python write_research_doc.py --vault-path P --input-file F`, `F: {"topic": str, "summary": str, "details": str, "source_url": str|null}`. Writes `Work/Research/<slug>.md` with frontmatter (`type: "ResearchDoc"`, `topic`, `tags: ["research"]`, `source_url` omitted if none, `created`) + `## Summary`/`## Details`. NEVER overwrites — a title collision gets a disambiguating suffix (mirroring `capture_note.py`'s own `_unique_note_path` time/counter-suffix technique), always a brand-new file.
- `Hermes-Provisioning/skills/librarian/research-kb-writer/SKILL.md` — documents the Skill for a real Hermes profile: when to use it (any research request, from any caller), how to call the script (plain `terminal` invocation, full absolute path, matching this codebase's established convention), and the explicit instruction that finding nothing conclusive means reporting honestly and NEVER calling this script.
- A real, live `research-agent` Hermes profile provisioned on the operator's actual Hermes install (Librarian Section, `web_search`/`terminal` tools, this Skill installed) — a live, Hermes-side action outside this repo's own version control (see Constraints), needed to verify Scenarios live.

---

## Files to Modify

- `Hermes-Provisioning/skills/librarian/research-kb-writer/scripts/write_research_doc.py` (new)
- `Hermes-Provisioning/skills/librarian/research-kb-writer/SKILL.md` (new)

---

## Constraints

- Inherits from parent story.
- The script's write is structurally confined to `Work/Research/` — it must be physically incapable of writing anywhere else (no destination-path argument beyond `--vault-path`, the `Work/Research/` segment is hardcoded).
- NEVER overwrite an existing file — every call creates a brand-new file, even on an exact title repeat (ONE deliberate divergence from `azure-kb-writer`'s own update-in-place contract, per `ADR-008`).
- No approval/confirmation step anywhere in the script or `SKILL.md`'s own instructions — the write proceeds immediately once called.
- The script takes no caller-identifying argument (topic/summary/details/source_url only) — same script, same contract, regardless of who/what is calling it.
- `SKILL.md` must explicitly instruct: if research finds nothing conclusive, report that honestly and do NOT call this script — no fabricated note.
- **Provisioning the real, live `research-agent` Hermes profile itself (SOUL.md, tool grants, Skill installation) is real, Hermes-side infrastructure work with no checked-in-repo file to diff** — per `ADR-008`'s own Consequences ("must be provisioned outside this repo... not part of this repo's own `src/` build") and this repo's own established precedent (`azure-kb-writer`/`compass-kb-writer`, the 3 Customer Experts — none checked in). This is authorized, expected work for this task's own live verification (mirroring this project's established pattern of the coder performing real environment/provisioning actions to prove a locked AC — e.g. real cron jobs created for `vault-rebuild`), not an escalation-triggering out-of-scope file change.

---

## Tests

**Manual verification steps:**
1. [REQ-SB-82-US-02-AC-01] Script-level (repo-buildable, real file I/O): call `write_research_doc.py` with a real scratch `--input-file` against a scratch vault path. Expect a real new file at `Work/Research/<slug>.md` with the documented frontmatter + `## Summary`/`## Details`.
2. [REQ-SB-82-US-02-AC-02] From the state left by step 1, confirm no other note anywhere in the scratch vault was touched (diff the vault's file listing/mtimes before and after).
3. [REQ-SB-82-US-02-AC-02] Call the script AGAIN with the same `topic`/title. Expect a SECOND, distinctly-named file created (suffix-disambiguated) — the original file from step 1 is untouched (confirm its content/mtime unchanged).
4. [REQ-SB-82-US-02-AC-03] Read the finished script top-to-bottom: confirm no approval/confirmation/pending-approval call exists anywhere in the write path — the file write is the last real action after validation.
5. [REQ-SB-82-US-02-AC-04] Read the finished script's own CLI contract (`argparse` definitions): confirm no caller-identifying argument exists — the same script/contract serves any caller.
6. [REQ-SB-82-US-02-AC-05] Read the finished `SKILL.md`: confirm it explicitly instructs honest "found nothing conclusive" reporting with no script call, for the no-conclusive-result case.
7. **Live, once the real `research-agent` profile is provisioned** — [REQ-SB-82-US-02-AC-01]/[REQ-SB-82-US-02-AC-04]: issue a real research request via `hermes -p research-agent chat -q "<test topic>"` and, separately, via a live relay from another profile (simulating a Cockpit-Chat-style caller). Confirm both produce a real new note in `Work/Research/` with equivalent behavior.
8. **Live** — [REQ-SB-82-US-02-AC-05]: issue a real research request for a deliberately obscure/unanswerable topic. Confirm the agent honestly reports finding nothing conclusive and no new file appears in `Work/Research/`.

**Automated tests:** `n/a — test tooling pending (only src/backend/tests/test_health_check.py exists today)`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `write_research_doc.py` implemented per Constraints (never overwrites, structurally confined to `Work/Research/`)
- [x] `SKILL.md` authored, including the honest-no-result instruction
- [x] Real `research-agent` Hermes profile provisioned live (Librarian Section, `web_search`/`terminal` tools, this Skill installed)
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Registering `research-agent` in Second Brain's own `agents_map_adapter.py` (`T01`).
- Any merge/dedup logic for repeated similar research requests.
- Wiring Research Agent output into the Cockpit Overview tab (`REQ-SB-82-US-05` or later).
- Routing through `REQ-SB-63`'s Vault Filing Expert (structurally not live today, per `ADR-008`).

---

## Context / Notes

`ADR-008` and architecture.md §Research Agent & Librarian Vault-Write Skill
are the authoritative design references. `capture_note.py`
(`Hermes-Provisioning/skills/notes-capture/capture-notes/scripts/`) is the
closest real precedent for this script's own CLI/frontmatter/collision-
avoidance shape — read it before starting, but note its no-overwrite
behavior comes from ALWAYS treating a same-title note as a new same-day
file (time-suffix), matching (not diverging from) what this task needs, so
its `_unique_note_path` technique can be reused directly rather than
`azure-kb-writer`'s own (out-of-repo, not readable) update-in-place
contract.

---

## Implementation Log

**2026-08-25, coder pass.** Built exactly per `## Files to Modify` and
`ADR-008`:

- `Hermes-Provisioning/skills/librarian/research-kb-writer/scripts/write_research_doc.py`
  — mirrors `write_azure_doc.py`'s own `--vault-path`/`--input-file` CLI
  contract and frontmatter/`## Summary`/`## Details` body shape. Write is
  structurally confined to `Work/Research/` (no destination-path argument
  beyond `--vault-path`; the segment is hardcoded). Never updates in
  place — reused `capture_note.py`'s own `_unique_note_path`
  time-then-counter disambiguation technique verbatim for the collision
  case (one deliberate divergence from `azure-kb-writer`, per `ADR-008`
  Decision 3). No approval/confirmation call anywhere in the write path.
  No caller-identifying CLI argument (`topic`/`summary`/`details`/
  `source_url` only).
- `Hermes-Provisioning/skills/librarian/research-kb-writer/SKILL.md` —
  documents the Skill for a real Hermes profile, including an explicit
  "if research finds nothing conclusive, report honestly and do NOT call
  this script" instruction.
- Real, live `research-agent` Hermes profile provisioned on the operator's
  actual Hermes install (`hermes profile create research-agent --clone`),
  under `C:\Users\<operator>\AppData\Local\hermes\profiles\
  research-agent\` — real SOUL.md authored (Librarian-Section identity,
  not meeting-scoped, "may itself grow into a full Expert... same way
  Compass/Azure Experts did", always writes a brand-new note into its own
  `Work/Research/`, no approval needed, uses Hermes' own bundled
  `web_search`/`terminal` tools directly, no caller-specific behavior);
  real description set via `hermes profile describe research-agent --text
  "..."` (confirmed live in the resulting `profile.yaml`,
  `description_auto: false`, matching every other real specialist's own
  convention); `research-kb-writer` Skill copied into the profile's own
  `skills/librarian/research-kb-writer/` (confirmed registered via
  `hermes -p research-agent skills list` — `librarian` category, `local`
  source, `enabled`). `.env` already carried the real
  `OBSIDIAN_VAULT_PATH=<OPERATOR_VAULT_OLD>` from clone-time
  inheritance (root `.env` fix, `MEMORY.md` 2026-08-25 entry) — confirmed
  directly by reading the cloned file, no manual edit needed; also stated
  explicitly in SOUL.md's own prose per every other real profile's
  established practice, not relied on via the env var alone.

**Verification (script-level, repo-buildable, real file I/O — steps
1-6):**

- **[REQ-SB-82-US-02-AC-01]** Called `write_research_doc.py` with a real
  scratch input file against a scratch vault
  (`.../scratchpad/vault_test`). Real output:
  `{"created": true, "path": ".../vault_test/Work/Research/LangGraph
  checkpointing.md"}`. Read the file back — real frontmatter
  (`type: "ResearchDoc"`, `topic`, `tags: ["research"]`, `created`,
  `source_url`) + `## Summary`/`## Details`, exactly as documented. **Pass.**
- **[REQ-SB-82-US-02-AC-02]** Before the call, hashed/timestamped a
  pre-seeded `Work/Existing/keep.md`. After the call, its hash and mtime
  were byte-identical — untouched. **Pass.**
- **[REQ-SB-82-US-02-AC-02]** Called the script AGAIN with the identical
  `topic` ("LangGraph checkpointing") but different `summary`/`details`.
  Real output: a SECOND, distinctly-named file
  (`LangGraph checkpointing 13-29.md`, time-suffixed). Re-hashed/
  re-timestamped the ORIGINAL file — byte-identical hash and mtime to
  before the second call; `Work/Existing/keep.md` also still untouched.
  **Pass.**
- **[REQ-SB-82-US-02-AC-03]** Read the finished script top-to-bottom: no
  approval/confirmation/pending-approval call exists anywhere in the write
  path — `note_path.write_text(...)` is the last real action after
  validation. **Pass.**
- **[REQ-SB-82-US-02-AC-04]** Read the finished script's own `argparse`
  definitions: only `--vault-path`/`--input-file`; the JSON payload only
  accepts `topic`/`summary`/`details`/`source_url` — no caller-identifying
  argument anywhere. **Pass.**
- **[REQ-SB-82-US-02-AC-05]** Read the finished `SKILL.md`: explicitly
  instructs "If your research genuinely finds nothing conclusive, report
  that honestly ... and do NOT call this script ... No note gets written
  for that request." **Pass.**

**Live verification (steps 7-8, once the real `research-agent` profile was
provisioned):**

- **[REQ-SB-82-US-02-AC-01]** `hermes -p research-agent chat -q "Research
  what LangGraph's checkpointing/persistence mechanism is and how it
  enables human-in-the-loop workflows..." -Q --create-if-missing -c
  "verify-research-agent"`. The agent ran real `web_search` lookups
  (LangChain/LangGraph docs), then called `write_research_doc.py` for
  real. Confirmed a genuine new file at `C:\myWorx\<operator vault>\Moussa
  Brain\Work\Research\LangGraph checkpointing-persistence and
  human-in-the-loop (HITL).md` — read back directly: real, substantive,
  cited content (LangChain/LangGraph doc URLs), not a fabrication. **Pass.**
- **[REQ-SB-82-US-02-AC-04]** Second real request relayed from a
  DIFFERENT profile (`hermes -p notes-manager chat -q "Use the terminal
  tool to run this exact command ... hermes -p research-agent chat -q
  \"Research what a race condition is...\" ..."`), simulating a
  Cockpit-Chat-style caller. Produced an equivalent, independently real
  new note (`Race condition in concurrent programming and a common
  prevention method (mutex-l.md`) with the same real frontmatter/body
  shape — confirmed both notes coexist in `Work/Research/` (2 files),
  proving the agent behaves identically regardless of which caller
  reached it. **Pass.**
- **[REQ-SB-82-US-02-AC-05]** Sent a deliberately unanswerable request
  (a fictitious "Xylonithex Corp Q3 2029 Innovation Summit" in a fictional
  town). Real reply: "Result: no verifiable record found; no note
  written" with an honest account of what was checked (vault search, web
  search, no matches) — confirmed `Work/Research/` still held exactly the
  same 2 files as before this call; no fabricated note appeared. **Pass.**

**Extra live confirmation beyond the task's own named steps:** hit the
real, running Agents Map API (`GET http://127.0.0.1:8001/agents`) after
provisioning — `research-agent` now appears with `"type": "expert"`,
`"section_id": "librarian"`, matching `T01`'s own (previously inert)
registration exactly. Confirms `T01`'s dict entries activate correctly
now that the real Hermes profile exists, end-to-end across both tasks.

**Scope-internal judgment call, disclosed:** the real, minimal test
research topics used above (LangGraph checkpointing, a race condition)
are deliberately unrelated to this codebase's own domain — chosen only to
be real, verifiable, concrete topics a live `web_search` could genuinely
resolve, per this project's own established "frame around something
genuinely real, not an obviously-empty query" verification precedent.

All 5 locked ACs (`AC-01`-`AC-05`) verified live with real, positive
results — no environment-blocked/deferred half.

gate: clear 2026-08-25 — no MUST-FLAG trigger fired (no new assumption
beyond what `ADR-008`/the story's own Notes already resolved; no new
dependency/interface change/ADR deviation; the real, live Hermes-side
provisioning work is pre-authorized by this task's own Constraints, not
an escalation-triggering out-of-scope file change; every locked AC
verified with a real positive result).
