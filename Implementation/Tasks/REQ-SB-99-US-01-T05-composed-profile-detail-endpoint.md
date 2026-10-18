---
id: REQ-SB-99-US-01-T05
title: business/hermes/profile_detail.py composes the five regions behind one route on the view-only mirror router
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: backend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement calls logged for human spot-check — the composition deliberately imports nothing from `app/hermes` (it passes the readers' own status/scope strings through rather than re-stating their constants), it reaches `client.config.home_path` so an unreadable install can name itself, a key set in BOTH config layers is reported as such rather than resolved, and a key missing from an unreadable layer is `unknown` rather than `not_set`. Plus one out-of-scope live FINDING: on a disposable install the app's own Action-catalogue publication rewrote a profile's SOUL.md and deleted its `## Scope` section body. Nothing blocked; no AC weakened."
phase: P2
depends_on: [REQ-SB-99-US-01-T01, REQ-SB-99-US-01-T02, REQ-SB-99-US-01-T03, REQ-SB-99-US-01-T04]
created: 2026-10-17
updated: 2026-10-18
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

- [x] One composing module + one route on the existing view-only mirror router
- [x] Five regions, each independently produced and independently honest
- [x] Three failure kinds reported as three different things
- [x] Nothing written anywhere; `deployed_to` never consulted
- [x] No cost added to any listing path
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not updated, deliberately**: every decision here is already written as
      `ADR-043` and in `architecture.md`, and a duplicate bullet would be noise
      in a file already over its own size budget
- [x] `CHANGELOG.md` entry appended

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

**2026-10-18 — Done.** Three files, exactly the three in `## Files to Modify`:
`src/backend/app/business/hermes/profile_detail.py` (new, the composition),
one new route on `src/backend/app/api/hermes_agents_router.py` (+23/−1), and
`src/backend/tests/test_profile_detail_view.py` (new, 20 tests). No file
outside that list was touched by the code change.

**File-list check, run before any code was written** (the standing rule, `fe4b0c1`
— "what single edit, in a file this task does not otherwise touch, is the
difference between this code existing and this code running?"): the switch-on
site is `app.include_router(hermes_agents_router)` in `src/backend/app/main.py`
line 249, which **already exists** — the new route hangs off a router that is
already mounted, so nothing else needed authorising and no escalation was
raised. The frontend half is `T06`'s by design.

### What was built

- `read_profile_detail(profile_id) -> dict | None` — one envelope, five
  independently-produced regions, each carrying its own `read` flag, its own
  payload and its own `error`. `None` means "the profile directory does not
  exist on a readable install", which is the route's 404 and the only 404.
- `GET /hermes/agents/{agent_id}/profile-detail` on the existing view-only
  mirror router. No new router file; `agents_router.py` untouched.
- Composition only: `read_soul_document()`, `compare_profile_skills()`,
  `read_config_layers()`, `cron_status.list_cron_jobs(profile_id)` and
  `cli.read_tools()`. Nothing here parses a `SKILL.md`, splits the soul,
  re-runs `_soul_excerpt`, merges config layers or calls `list_tools`, and
  `deployed_to` is never read.
- Config keys: one row per key, each naming the file its value came from,
  with `source` being the layer's own `scope` for a key set in exactly one
  layer, `set_in_more_than_one_layer` when both files set it, `not_set` when
  no readable layer does, and `unknown` when a layer could not be read at all.
  No merged or effective value exists anywhere in the response.

### Verification — automated mode, every locked AC tagged in the test file

Baseline measured on this exact tree at `91655ba` with only the new test file
excluded: **576 passed, 0 failed, 21.16s**. After this task: **596 passed, 0
failed, 27.24s** (+20, exactly this file's tests). Both named flakes
(`test_health_check.py::test_health_reports_the_commit_the_running_code_was_loaded_from`,
`test_marketplace_source.py`) passed.

| AC-ID | Test (`tests/test_profile_detail_view.py`) | Observed |
|---|---|---|
| `AC-01` | `test_the_soul_region_is_the_file_itself_and_the_excerpt_surfaces_are_untouched` | **Pass.** `soul.text` equals the fixture `SOUL.md` byte-for-byte; `## Scope`'s prose body present; `## Guardrails` < `## Scope` < `## Escalation` index order holds; length 685 > 280; `soul.path` is that profile's own file; `(read, status, error) == (True, "read", "")`. `GET /agents/adnoc-expert` still returns `description == "The adnoc-expert profile."` and `GET /hermes/agents/adnoc-expert` the same `description`/`short_description`, neither equal to the soul. |
| `AC-02` | `test_every_deployed_skill_appears_with_its_version_and_verdict` | **Pass.** All four on-disk skills listed with deployed versions `1.0.0` / `0.9.0` / `2.0.0` / `0.1.0` and statuses `current` / `stale` / `modified` / `unknown_to_framework`; the catalog-unknown row carries `catalog_version: None`. |
| `AC-02` | `test_the_view_adds_no_second_opinion_to_the_skills_verdict` | **Pass.** The region's `items` compare **equal** to `SkillManager.compare_profile_skills("adnoc-expert")` called directly — the view adds nothing and re-derives nothing. |
| `AC-03` | `test_config_is_two_labelled_layers_with_every_key_naming_its_own_file` | **Pass.** Two layers in order `profile`, `install_root`, each naming its real file and holding only its own file's mapping. `model.default = "gpt-5"` → source `profile` (set here); `model.provider = "custom"` and `logging.level = "info"` → source `install_root` (inherited from the install root); `agent.reasoning_effort` → `not_set`, value and path `None`. Every row names its file. |
| `AC-03` | `test_the_enabled_toolsets_come_from_the_honest_read` | **Pass.** `{"vault": True, "outlook": True, "web_search": False}` from `read_tools`, `read: true`, empty error. |
| `AC-03` | `test_no_merged_or_effective_config_value_exists_anywhere_in_the_response` | **Pass.** Every key name in the whole response tree, recursively, scanned for `merged`/`effective`/`resolved` — none; and neither layer carries the other's keys. |
| `AC-04` | `test_the_profiles_own_jobs_and_the_install_level_ones_are_never_merged` | **Pass.** `items == [A1]` with `schedule_display "every day at 07:00"`, `last_status "failed"`, `last_run_at` present, `scope "profile"`; `R1` is **not** in it and **is** in `install_level` with `scope "install"`. |
| `AC-04` | `test_the_existing_cron_endpoint_is_untouched` | **Pass.** `GET /hermes/cron/jobs` returns `[R1]` only and equals `cron_status.list_cron_jobs()` — install-root-only, exactly as `T02` left it. |
| `AC-04` | `test_the_primary_profile_does_not_list_its_own_jobs_twice` | **Pass.** `default` → `items == [R1]`, `install_level == []`, `install_level_is_this_profile is True`. |
| `AC-05` | `test_opening_refreshing_and_leaving_the_view_writes_nothing` | **Pass.** Every path under `tmp_path` hashed (sha256 + mtime, directories included) before and after **three** requests — snapshots identical, nothing created, nothing removed. |
| `AC-05` | `test_the_view_writes_no_registry_record` | **Pass.** `skills_data.write_skill_md` / `write_section_access_map` / `delete_skill_dir` / `write_script` are monkeypatched to raise for every test in the file (none fired), and the Skill store's own file is pinned byte- and mtime-identical across a request. |
| `AC-06` | `test_three_broken_reads_are_three_different_answers_in_one_response` | **Pass.** One response: soul `(read False, status "absent", text None)` naming the missing file; profile config layer `status "unreadable"`, `values None`, naming the file, while the **root layer still returns its real values**; `model.default` becomes `unknown` rather than `not_set`; toolsets `read False`, `items None` (not an empty mapping) carrying the real failure text; skills still all four verdicts and cron still `[A1]`; `install.readable` still true. |
| `AC-06` | `test_an_empty_soul_is_a_successful_read_and_not_an_absent_one` | **Pass.** `(True, "read", "", "")` — the fourth answer, distinct from absent. |
| `AC-06` | `test_a_profile_that_does_not_exist_on_a_readable_install_is_a_404` | **Pass.** 404 naming the id. |
| `AC-07` | `test_an_unreadable_install_reports_itself_and_fabricates_no_region` | **Pass.** HTTP **200** (not 404); `install.readable false` with the path in the message; all five regions `read: false` with a non-empty error; `soul.status == "not_read"` and `text None`; `skills.items`, `config.layers`, `config.keys`, `cron_jobs.items`, `cron_jobs.install_level` and `toolsets.items` all `None` — no empty list or mapping presented as a read; the absent install directory was not created. |
| `constraint: cost` | `test_one_request_costs_one_toolsets_read_and_one_skills_listing` | **Pass.** See the numbers below. |
| `constraint: cost` | `test_the_listing_endpoints_pay_nothing_for_this_view` | **Pass.** See the numbers below. |
| `constraint: cost` | `test_a_failed_toolsets_read_is_not_retried` | **Pass.** One `read_tools` call when the subprocess fails — reported, never retried. |

### Cost, pinned by equality (`BUG-086`)

Measured by wrapping the real `cli.read_tools`, `skills.get_all` and
`skills.read` on the live client and the catalog reader — recording **which
profile each call was for**, because a bare count cannot catch "once per
profile on the install", which is the shape `BUG-086` measured.

| Request | `read_tools` | skills listing | catalog reads | deployed-byte reads |
|---|---|---|---|---|
| `GET /hermes/agents/adnoc-expert/profile-detail` | `["adnoc-expert"]` (1) | `["adnoc-expert"]` (1) | 4 — one per distinct slug on disk | 3 — none for the slug the catalog lacks |
| `GET /agents` | `[]` (**0**) | `[]` (**0**) | `[]` | `[]` |
| `GET /hermes/agents` | `[]` (**0**) | `["default", "adnoc-expert"]` — **unchanged**, the mirror's pre-existing per-profile listing | `[]` (**0** comparisons) | `[]` |

Each row is asserted by **list equality**, not by a bound. The zero-added-cost
proof on the two listing endpoints is therefore two-sided: zero `hermes tools
list` subprocesses on either, zero skills comparisons on either, and the one
pre-existing listing cost on `GET /hermes/agents` pinned at exactly what it
was so this story is shown to have added nothing to it.
`tests/test_agent_listing_cost.py` passed **unchanged**.

### Where reads, writes, subprocesses and outbound calls land

Proved before trusting the suite:

- `subprocess.run` **and** `subprocess.Popen` are refused for the whole test
  file by an autouse fixture — **0** real spawns; the one command this view
  makes is faked at `HermesCLI._run`.
- conftest's suite-wide Hermes sandbox is **asserted, not assumed**
  (`settings.hermes_home_path` is this test's own `tmp_path` install), and was
  neither weakened nor special-cased.
- Every `Path.read_text` during a full composed request is recorded and proved
  to lie under `tmp_path` — **0** reads outside it.
- Every catalog/Registry write function is monkeypatched to raise — **0**
  fired.
- The whole `tmp_path` tree is hash-identical across three requests.
- **Live check on a disposable instance, port 8017** (own Hermes home, own
  vault, own data path, all under the scratchpad), started with the Hermes
  `bin` directory **removed from its PATH** — `_hermes_exe()` falls back to
  `shutil.which("hermes")`, which on this machine resolves to the operator's
  real install, so stripping it is what kept a real `hermes tools list` from
  ever running. The operator's backend on `:8001` was never called and was
  still listening afterwards. Observed there: the soul **verbatim** (equal to
  the file on disk), both config layers with per-key sources
  (`profile` / `install_root` / `not_set`), the profile's `A1` separate from
  the install-level `R1`, a real skills verdict against the **real shipped
  catalog** (`vault-index` deployed `1.0.0` vs catalog `0.1.0` → `stale`),
  toolsets honestly `read: false` with "No real Hermes install found…" rather
  than an empty mapping, a 404 for an unknown profile, and — after a restart
  pointed at a non-existent home — a **200** with `install.readable false`,
  every region unread and the absent directory still absent.

### Judgement calls (scope-internal — `gate: flagged` for spot-check)

1. **The composition imports nothing from `app/hermes`.**
   `business/hermes/client.py` states it is the only file in the app allowed
   to, and it has **zero** exceptions today. So rather than importing
   `FILE_WAS_READ` / `CONFIG_LAYER_PROFILE` / `CONFIG_LAYER_INSTALL_ROOT`,
   the view passes each reader's own `status` / `scope` string **through**
   and decides "did this read succeed" structurally (`text is None`,
   `values is None`). It therefore holds no copy of those names to drift, and
   needs no ordering assumption about the layers either. The test file imports
   the constants by name and pins them. The alternative — re-exporting them
   through `client.py` — would have meant a file outside this task's list.
2. **`client.config.home_path` is read for the install path** — the first use
   of `client.config` outside the library. `install_is_readable()` returns
   only a bool, and `AC-07` asks the view to *name why*; taking the path from
   `settings` instead could name a directory other than the one the readers
   actually used, which would be a lie on the one screen built to stop lies.
3. **Existence is checked with `profiles.get_all(include_skills=False)`, not
   `find_by_id`.** `find_by_id` reads the profile's skills a second time,
   which would break the one-listing-per-request cost pin. It also yields
   `is_primary`, which is how the view knows a profile IS the install root
   without a fourth hand-copy of the `"default"` convention.
4. **A key set in BOTH layers is `set_in_more_than_one_layer`**, with both
   occurrences and no single value. The ACs only require set-here / inherited
   / not-set, but choosing one when both files set a key is exactly the merged
   guess `ADR-043` forbids.
5. **A key missing from a layer that could not be read is `unknown`, not
   `not_set`** — the same honesty rule one level down; a file we failed to
   read may well set it.
6. **Each region is produced inside a broad `except Exception`.** Deliberate
   and commented: the locked constraint is that one region's failure never
   aborts another's, and a debugging view that dies whole is worth nothing.
7. **Nothing added to `MEMORY.md`** — every decision here is already `ADR-043`
   and `architecture.md`.

### Out-of-scope finding (not fixed here, not a defect of this task)

On the **disposable** install, the app's own startup Action-catalogue
publication **rewrote** `profiles/adnoc-expert/SOUL.md`: the file came back
with its `## Scope` section **gone entirely** — prose body and all — its
remaining sections reordered, and the action-catalogue marker block inserted.
This endpoint reported the file verbatim as it then stood, which is correct
behaviour and is how the loss became visible. It means the lossiness
`REQ-SB-99` documents is not only a read-path problem: a publication **write**
destroys `## Scope` prose on disk. Nothing was changed about it here — it is
outside this task's files and its story — and it is raised in `REVIEW-QUEUE.md`
for the operator to decide whether it becomes a `BUG`.
