---
id: REQ-SB-99-US-01-T05
title: business/hermes/profile_detail.py composes the five regions behind one route on the view-only mirror router
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Ready
gate: clear
gate_reason: ""
phase: P2
depends_on: [REQ-SB-99-US-01-T01, REQ-SB-99-US-01-T02, REQ-SB-99-US-01-T03, REQ-SB-99-US-01-T04]
created: 2026-10-17
updated: 2026-10-17
---

# REQ-SB-99-US-01-T05 — One Composed Read, One Route

## Parent Story

- Story: [[REQ-SB-99-US-01]] — `../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-99 *See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs*

---

## Objective

Compose the five regions — soul, skills-with-verdicts, config layers, bound
cron jobs, toolsets — into one read-only response behind one new route, with
the three ways a read can fail reported as three different things.

---

## Starting State → End State

**Before / Inputs:**

- `T01` gives `SkillManager.compare_profile_skills(profile_id)` (install-first,
  five statuses, one shared verdict rule).
- `T02` gives `cron_status.list_cron_jobs(profile_id)` plus the
  `scope: install | profile` label.
- `T03` gives `HermesCLI.read_tools(profile_id)` → `(succeeded, mapping, message)`.
- `T04` gives `HermesProfiles.read_soul_document()`, `read_config_layers()` and
  `install_is_readable()`.
- `src/backend/app/api/hermes_agents_router.py` is the view-only mirror of
  Hermes' own files (`prefix="/hermes"`, two routes today) and is where install
  truth belongs (`ADR-003`).
- `src/backend/app/business/hermes/agents_map_adapter.py` is the shape to
  follow: a composing module inside `business/hermes` that reaches Managers and
  `get_client()`, never `data_access`.

**After / Outputs:**

- `src/backend/app/business/hermes/profile_detail.py` — one public function,
  e.g. `read_profile_detail(profile_id: str) -> dict`, returning an envelope
  whose top level mirrors `business/hermes/status.py`'s honest convention and
  whose regions each carry their own outcome:

  ```
  {
    "profile_id": ..., "install": {"readable": bool, "error": str | None},
    "soul":     {"path": ..., "text": str | None, "error": str | None},
    "skills":   {"items": [...], "error": str | None},
    "config":   {"layers": [{"source": "profile"|"install_root", "path": ...,
                             "values": {...} | None, "error": ...}],
                 "keys": [{"key": ..., "value": ..., "source": "profile"
                           | "install_root" | "not_set", "path": ...}]},
    "cron_jobs": {"items": [...], "install_level": [...], "error": ...},
    "toolsets":  {"read": bool, "items": {...}, "error": str | None}
  }
  ```
  (shape indicative; the regions, their independence and their honesty are the
  contract, the exact key names are the coder's.)

- Each config key shown names the file it came from; a key present only in the
  install-root layer is `source: "install_root"` (inherited from the install
  root), a key in neither is `source: "not_set"`. **No merged effective value
  is produced.**
- `GET /hermes/agents/{agent_id}/profile-detail` on the existing router —
  `404` only when the profile directory genuinely does not exist on a readable
  install; an unreadable install is a `200` whose `install.readable` is `false`
  and whose every region is unread, never fabricated.
- Cron jobs: the profile's own jobs under `items`, plus the install-level jobs
  (root `scope: "install"`) surfaced separately so they are visible somewhere
  rather than nowhere — never merged into the profile's own list.

---

## Files to Modify

- `src/backend/app/business/hermes/profile_detail.py` (new) — the composition.
- `src/backend/app/api/hermes_agents_router.py` — one new route.
- `src/backend/tests/test_profile_detail_view.py` (new) — the tests below.

---

## Constraints

- Inherits from parent story.
- **Compose, never re-derive.** The view calls `T01`–`T04`'s functions. It must
  not parse a `SKILL.md`, read skill bytes, split the soul into marker blocks,
  re-run `_soul_excerpt`, merge config layers, or call `cli.list_tools` instead
  of `read_tools`. A second answer to a question the codebase already answers
  is the failure this story exists to avoid (`ESC-066`, `Learnings.md`).
- **`deployed_to` is not consulted on this path at all** — the view cannot
  inherit the untrustworthiness `REQ-SB-96` exists to fix, and this story
  creates no dependency on `REQ-SB-96`.
- **Strictly read-only** (`ADR-003`): no persistence, no cache, no write into
  `<HERMES_HOME>`, no Registry mutation, no `deployed_to` reconciliation as a
  side effect of looking.
- **The cost is paid here and nowhere else.** Exactly one `hermes tools list`
  subprocess and one profile's skills comparison per request; nothing added to
  `GET /agents`, `GET /hermes/agents`, or the Agents Map's mount-time fetches
  (`BUG-086`).
- Layering: `business/hermes` reaches Managers and `get_client()`, never
  `data_access` (`ADR-003`). No new router file; do not touch
  `agents_router.py`, and do not extend `GET /agents/{id}/jobs` (that is the
  Pipeline job tree).
- One region's failure never aborts another's — every region is produced inside
  its own guard.

---

## Tests

**Automated tests:** `cd src/backend; pytest tests/test_profile_detail_view.py tests/test_agent_listing_cost.py`

Build a real temporary Hermes home with `tmp_path` (root `SOUL.md`/`config.yaml`/
`cron/jobs.json`; `profiles/adnoc-expert/` with its own `SOUL.md`,
`config.yaml`, `skills/<cat>/<slug>/SKILL.md` and `cron/jobs.json`), construct a
real `HermesClient` over it and install it with
`monkeypatch.setattr(client_module, "_client", real_client)`; monkeypatch
`HermesCLI._run` for the toolsets text. Drive the route with
`httpx.ASGITransport(app=app)` or `TestClient` — the established techniques.

1. `[REQ-SB-99-US-01-AC-01]` `GET /hermes/agents/adnoc-expert/profile-detail`;
   assert `soul.text` equals the fixture's `SOUL.md` byte-for-byte, including
   the `## Scope` body and section order, is longer than 280 characters, and
   that `soul.path` names that profile's own file. Assert
   `GET /agents/adnoc-expert` still returns its existing `description` /
   `short_description` unchanged.
2. `[REQ-SB-99-US-01-AC-02]` With the fixture's profile holding a current, a
   stale, a modified and a catalog-unknown skill, assert the `skills` region
   lists all four with their deployed versions and statuses
   (`current`/`stale`/`modified`/`unknown_to_framework`), and that the row
   values are exactly what `SkillManager.compare_profile_skills("adnoc-expert")`
   returns called directly — i.e. the view added no second opinion.
3. `[REQ-SB-99-US-01-AC-03]` Assert the `config` region returns two layers, each
   naming its real file; that a key set only in the root layer is reported with
   `source` meaning *inherited from the install root*, a key set on the profile
   with `source` meaning *set here*, and a key in neither as *not set*; that the
   model and provider recorded for the profile appear; that the enabled toolsets
   appear from `read_tools`; and that **no** merged/effective mapping key exists
   anywhere in the response.
4. `[REQ-SB-99-US-01-AC-04]` With job `A1` in `profiles/adnoc-expert/cron/jobs.json`
   and job `R1` only in `<home>/cron/jobs.json`, assert the profile's own list
   contains exactly `A1` with its schedule and last-run outcome, that `R1` is
   **not** in it, and that `R1` is present in the separate install-level list.
   Assert `GET /hermes/cron/jobs` returns exactly what it returned before this
   story.
5. `[REQ-SB-99-US-01-AC-05]` Snapshot every file under `tmp_path` (relative
   path → sha256 + mtime) before the request; issue the request three times
   (open, refresh, leave); re-snapshot and assert the two snapshots are
   identical and that no file or directory was created or removed. Additionally
   assert the request wrote no Registry record: pin the Skill store's own file
   (or `skills_data`'s write functions, monkeypatched to raise) untouched.
6. `[REQ-SB-99-US-01-AC-06]` Delete the profile's `SOUL.md`, corrupt its
   `config.yaml`, and make `_run` fail for `tools list`. Assert in one response:
   the soul region reports the missing file by name with no text, the config
   region reports the unreadable file by name while the root layer still
   returns its values, the toolsets region reports `read: false` with the real
   failure message and **not** an empty "nothing enabled" mapping, and the
   skills and cron regions still return their real content.
7. `[REQ-SB-99-US-01-AC-07]` Point the client's `home_path` at a path that does
   not exist. Assert the response reports the install as unreadable, names why,
   and that every region is explicitly unread — no region carries fabricated
   content, no empty list is presented as a successfully-read empty region.
8. `[constraint: cost]` Count calls on the real client's seams (wrap
   `cli.read_tools` and `skills.get_all` with counting spies): assert one
   `read_tools` call and one `skills.get_all` call, both for this profile only,
   per request — never one per profile on the install. Then assert
   `GET /agents` and `GET /hermes/agents` trigger **zero** `read_tools` calls
   and zero skills comparisons, and that `tests/test_agent_listing_cost.py`
   passes unchanged (`BUG-086`).

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] One composing module + one route on the existing view-only mirror router
- [ ] Five regions, each independently produced and independently honest
- [ ] Three failure kinds reported as three different things
- [ ] Nothing written anywhere; `deployed_to` never consulted
- [ ] No cost added to any listing path
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- The screen — `T06`.
- Any edit surface (soul, config, skills, jobs) — the story is a debugger, not
  a second editor.
- Making `GET /hermes/cron/jobs` install-wide, or any `deployed_to` repair —
  `REQ-SB-96`.
- Caching or persisting any of this.

---

## Context / Notes

`architecture.md` → **§One Composed Read**, **§Honest Absence — Three Different
Failures**, **§Cron Jobs — Binding Is a Directory, Not a Field**, **§Config as
Two Labelled Layers**, and `ADR-043`. Note `GET /hermes/agents/{id}` already
returns each skill with its version and `GET /agents/{id}` already pays the
`hermes tools list` subprocess — this route exists because it needs the
*verdict* and the *honest* toolsets read, not because those reads are new.

---

## Implementation Log

_(Filled in by the coder.)_
