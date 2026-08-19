---
id: REQ-SB-43-US-01-T05
title: New app/api/cockpit_router.py — GET /cockpit/{subject_kind}/{stem}, bring-in, message, research, research/save; registered in main.py
parent_story: REQ-SB-43-US-01
requirement_id: REQ-SB-43
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-43-US-01-T02, REQ-SB-43-US-01-T03, REQ-SB-43-US-01-T04]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-43-US-01-T05 — `app/api/cockpit_router.py`

## Parent Story

- Story: [[REQ-SB-43-US-01]] — `../UserStories/REQ-SB-43-US-01-meeting-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-43 *Meeting Cockpit — Expert-Assisted Meeting Workspace*

---

## Objective

New `APIRouter(prefix="/cockpit")` composing `T02`/`T03`/`T04`'s three cockpit submodules into the real HTTP surface both `MeetingCockpitPage.tsx` (this story) and `InboxCockpitPage.tsx` (`REQ-SB-44-US-01`) call — generic over `subject_kind: "meeting" | "email"`, never two parallel per-kind routers (`ADR-036` point 2).

---

## Starting State → End State

**Before / Inputs:** `T02`'s `threads.get_thread`/`bring_in_agent`/`send_user_message`; `T03`'s `people.resolve_people_chips`; `T04`'s `research.trigger_research`/`save_research_result`/`list_research_results`; `app.business.vault_indexing.get_index()`.

**After / Outputs:** new `app/api/cockpit_router.py`:
```python
from fastapi import APIRouter, HTTPException

from app.business import vault_indexing
from app.business.cockpit import people, research, threads

router = APIRouter(prefix="/cockpit")


def _subject_frontmatter(subject_note_stem: str) -> dict:
    entry = vault_indexing.get_index().get(subject_note_stem)
    if entry is None:
        raise HTTPException(status_code=404, detail="Unknown note")
    return entry["frontmatter"]


@router.get("/{subject_kind}/{subject_note_stem}")
def get_cockpit(subject_kind: str, subject_note_stem: str) -> dict:
    frontmatter = _subject_frontmatter(subject_note_stem)
    return {
        "subject": frontmatter,
        "people": people.resolve_people_chips(subject_kind, subject_note_stem),
        "thread": threads.get_thread(subject_kind, subject_note_stem),
        "research_results": research.list_research_results(subject_kind, subject_note_stem),
    }


@router.post("/{subject_kind}/{subject_note_stem}/bring-in")
def bring_in(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return threads.bring_in_agent(subject_kind, subject_note_stem, body["agent_id"])


@router.post("/{subject_kind}/{subject_note_stem}/message")
async def send_message(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return await threads.send_user_message(subject_kind, subject_note_stem, body["message"])


@router.post("/{subject_kind}/{subject_note_stem}/research")
async def trigger_research(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return await research.trigger_research(
        subject_kind, subject_note_stem, body["requesting_agent_id"], body["query"]
    )


@router.post("/{subject_kind}/{subject_note_stem}/research/save")
def save_research(subject_kind: str, subject_note_stem: str, body: dict) -> dict:
    return research.save_research_result(subject_kind, subject_note_stem, body["query"], body["summary"])
```
`app/main.py` gains:
```python
from app.api.cockpit_router import router as cockpit_router
...
app.include_router(cockpit_router)
```

---

## Files to Modify

- `src/backend/app/api/cockpit_router.py` (new) — per the code block above.
- `src/backend/app/main.py` — add the import and `app.include_router(cockpit_router)` line, additive.

---

## Constraints

- Generic over `subject_kind` in every route — no `if subject_kind == "meeting": ... else: ...` branching inside this router; `T02`/`T03`/`T04`'s own submodules are already generic (`ADR-036` point 2).
- `GET /cockpit/{subject_kind}/{subject_note_stem}` `404`s for an unknown/unindexed stem — never a fabricated empty subject.
- No route in this router calls `skill_registry.invoke_skill`/`_invoke_action` directly — every real invocation is inside `T02`/`T04`'s own submodules (`ADR-036` point 4).
- Request bodies are plain `dict` (no Pydantic model defined by this task) — matches this codebase's existing convention where a route's body shape is simple and stable (mirrors several existing routers' own plain-`dict` POST bodies); do not over-engineer a schema class for this pass.
- Discard has NO route — the frontend simply never calls `research/save` for a discarded result (`T04`'s own Constraint).

---

## Tests

**Manual verification steps** (real dev server: `.venv\Scripts\uvicorn app.main:app --reload --port 8001`, backend `.venv`; requires a real, indexed Meeting note stem and a real routable agent pairing, per `T04`'s own Tests):
1. **[REQ-SB-43-US-01-AC-02]**/**[REQ-SB-43-US-01-AC-04]** `GET /cockpit/meeting/<real-stem>` — confirm `200`, `subject` carries real frontmatter (subject/time/customer), `people` is a real list (per `T03`), `thread`/`research_results` are present (empty lists/seeded-empty thread if none yet).
2. Non-AC smoke check: `GET /cockpit/meeting/does-not-exist` → `404`.
3. **[REQ-SB-43-US-01-AC-05]** `POST /cockpit/meeting/<stem>/bring-in` with `{"agent_id": "vault-qa"}` — confirm `200`, `brought_in_agent_ids` includes `"vault-qa"`. Re-fetch `GET /cockpit/meeting/<stem>` — confirm the same.
4. **[REQ-SB-43-US-01-AC-05]**/**[REQ-SB-43-US-01-AC-06]** `POST /cockpit/meeting/<stem>/message` with `{"message": "What's Acme's renewal history?"}` — confirm `200`, `thread.messages` gained a real user turn and a real `vault-qa`-attributed reply.
5. **[REQ-SB-43-US-01-AC-08]** `POST /cockpit/meeting/<stem>/research` with `{"requesting_agent_id": "vault-qa", "query": "Acme Corp's Q3 earnings"}` — confirm an honest `found`/`no_results`/`no_match` response.
6. **[REQ-SB-43-US-01-AC-09]** `POST /cockpit/meeting/<stem>/research/save` with `{"query": "Acme Corp's Q3 earnings", "summary": "<real summary>"}` — confirm `200`, `note_path` populated, the file real on disk.
7. Clean-up: delete the saved research note and the test thread entry from `.second-brain/cockpit_threads.json`. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `GET /cockpit/{subject_kind}/{stem}` returns subject/people/thread/research_results, `404`s for an unknown stem
- [ ] `POST .../bring-in`, `.../message`, `.../research`, `.../research/save` compose `T02`/`T03`/`T04` correctly
- [ ] No route branches on `subject_kind` internally
- [ ] Registered in `app/main.py`
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend change — `T06`-`T09`.
- `REQ-SB-44-US-01`'s own attachment-review route addition — that story's own task, additive to this same router file.

---

## Context / Notes

Full mechanism: `ADR-036` points 2/3. `REQ-SB-44-US-01`'s own attachment-review task ADDS a new route to this SAME file (`GET/POST /cockpit/email/{stem}/attachments...`), not a second router — read this task's own real, as-built file before that story's task edits it.

---

## Implementation Log

Implemented exactly as spec'd — `app/api/cockpit_router.py` (new) + `app/main.py`
import/`include_router` addition. Composes `T02`/`T03`/`T04` unchanged.

**Real dev-server hit a genuine, project-precedented `--reload` staleness bug
during this task's own verification, resolved per the already-documented
protocol (`Implementation/Learnings.md`, `SPRINT-035`):** after editing
`main.py`/creating `cockpit_router.py`, `WatchFiles` logged "Reloading..." but
never logged a new "Started server process" line — the old worker kept serving
(a bare `404 Not Found` for a REAL, indexed stem, not our own honest
`HTTPException(404, "Unknown note")`). Killed both the reloader parent and its
still-alive old worker PID, started ONE fresh **non**-`--reload` instance for
the rest of this sprint's HTTP-level verification (`T05`-`T09`), per the exact
documented fix. Also found the fresh instance's own in-memory
`vault_indexing` index was empty until a manual `POST /vault-index/rebuild` —
expected (index is per-process, in-memory only, `ADR-024`; the app-start
scheduler tick rebuilds it too, this manual call was simply faster during live
verification).

**Manual verification (real HTTP, fresh instance on port 8001, real vault,
temporary real state changes reverted, same protocol as `T04`):**
1. **AC-02/AC-04:** `GET /cockpit/meeting/0-2026-08-10-CC920000` → `200`, real `subject` frontmatter, `people`/`thread`/`research_results` all present (empty — this real Meeting note carries no `attendees` field, per `T03`'s own disclosed finding). Confirmed.
2. Non-AC: `GET /cockpit/meeting/does-not-exist` → `404`. Confirmed.
3. **AC-05:** `POST .../bring-in` `{"agent_id":"vault-qa"}` → `200`, `brought_in_agent_ids` includes `"vault-qa"`; re-`GET` confirms the same. Confirmed.
4. **AC-05/AC-06:** `POST .../message` → `200`, real `vault-qa`-attributed reply appended (real Compass call, honest "couldn't find Acme" answer). Confirmed.
5. **AC-08:** `POST .../research` with no grant yet → honest `{"status":"no_match"}` (the only brought-in-relevant candidate, `vault-qa`, was itself the requester and is excluded from its own candidate pool — genuinely honest, not a bug). Re-ran with `requesting_agent_id: "compass-expert"` after the same temporary `vault-qa` grant/Provider-swap `T04` used → real `{"status":"found", "summary": <genuine Anthropic web-search result>, ...}`. Confirmed both paths honest.
6. **AC-09:** `POST .../research/save` → `200`, real `note_path`, file confirmed real on disk under `Work/Research/`. Confirmed.
7. Cleanup: saved note + `.second-brain/cockpit_threads.json` test entries deleted; `vault-qa`'s temporary grant/Provider reverted and independently reconfirmed via fresh `GET` calls.

gate: clear 2026-08-14 — no triggers fired (composes `T02`/`T03`/`T04` unmodified;
the `--reload` staleness issue is an already-documented, already-solved
operational finding, not a new assumption/dependency/ADR deviation).
