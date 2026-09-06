# BUGS.md

The append-only **source of truth** for bugs found through manual testing — UI
issues and logic issues alike. Detail lives here; `BACKLOG.md`'s `## Bugs` section
is a thin status mirror of the index table below.

- **Capture:** `/bug` (interactive — asks clarifying questions, then writes a row
  here at `Open`).
- **Fix:** `/triage` batches chosen `Open` bugs into one `BUGFIX-NN-US-01` story;
  that story then flows through `/plan-tasks → /plan-sprints → /implement-sprint`.
- **Full contract:** `Implementation/Pipeline.md` → "Bug tracking".

## Rules

- **Append-only.** Never delete a row or a detail subsection.
- `BUG-NNN` ids are **sequential and never reused** (even for `Won't Fix` bugs).
- This file is the source of truth; the `BACKLOG.md` `## Bugs` mirror is derived.
  Whoever changes a bug's status updates **both** in the same touch.
- **Area:** `UI | Logic`. **Severity:** `Blocker | Major | Minor | Cosmetic`.
- **Status:** `Open` (logged, no fix story) → `In Sprint` (a `BUGFIX-NN` story
  covers it, set at `/triage`) → `Closed` (covering story `Done`). Terminal:
  `Won't Fix` (with a reason in the detail subsection; never auto-set).
- A bug against already-`Done` work becomes **new forward work** (a `BUGFIX-NN`
  story), never a reopening of the original story.

---

## Index

| ID | Title | Area | Severity | Status | Found | Fixed by |
|---|---|---|---|---|---|---|
| BUG-043 | `hermes.exe` is looked for one directory too deep, so every Hermes CLI operation fails on a correct install | Logic | Blocker | Open | 2026-09-07 | — |
| BUG-044 | A failed Blueprint install leaves the Section it created behind | Logic | Major | Open | 2026-09-07 | — |
| BUG-045 | An unhandled 500 reaches the browser as `TypeError: Failed to fetch`, hiding every server error from the UI | Logic | Major | Open | 2026-09-07 | — |

> **Emptied 2026-09-06 (operator-directed), starting a clean cross-device build.**
> This file carried 42 bugs / 2,054 lines, 19 of them still `Open` and the oldest
> from 2026-08-11 — against a codebase that has since been restructured
> (`ADR-019`), with several naming code that no longer exists (`graph.py::_call_model`,
> `_MIGRATION_GRANT_SEED`, `compass_client.classify_email`, `propose_person_note_update`
> are all gone). Re-verifying each against the current build would have cost more
> than re-finding whichever still reproduce.
>
> **Nothing is lost** — the full ledger is in git at `d64dcb4`:
>
> ```bash
> git show d64dcb4:BUGS.md
> ```
>
> **The next id is `BUG-043`.** Ids are sequential and never reused, so do NOT
> restart at 001: the historical ids above are still referenced from
> `BACKLOG.md`, sprints, and commit messages.
>
> This empties the ledger; it does not close the bugs. Anything still real will
> be found again by the build it affects, and logged fresh via `/bug`.

---

### BUG-043 — `hermes.exe` is looked for one directory too deep, so every Hermes CLI operation fails on a correct install

- **Area:** Logic
- **Severity:** Blocker
- **Status:** Open
- **Found:** 2026-09-07, first real Blueprint install on this machine.
  `POST /blueprints/librarian/install` → 500,
  `HermesUnavailableError: hermes profile create failed: No real Hermes install
  found at the configured home path` — on a machine with a healthy Hermes
  (`hermes --version` works, gateway running).
- **Root cause:** `src/backend/app/hermes/cli.py:48`

      exe = self._config.home_path / "hermes-agent" / "bin" / "hermes.exe"

  Verified on disk:

      <home>/hermes-agent/bin/hermes.exe   NOT THERE
      <home>/bin/hermes.exe                FOUND

  `hermes-agent/` is the cloned repo; `bin/` is its **sibling**, not its child.
- **Already known in documentation, never fixed in code.** `Deployment.md`
  carries this exact correction: *"the `hermes` executable is at
  `%LOCALAPPDATA%\hermesin\hermes.exe` — not
  `%LOCALAPPDATA%\hermes\hermes-agentin\hermes.exe`"*, naming
  `REQ-SB-85-US-02-T01` as where the wrong path was recorded. The doc was
  corrected; `cli.py` was not.
- **Expected:** the CLI resolves against a real install and `hermes profile
  create` succeeds.
- **Actual:** `_hermes_exe()` returns `None`, so `_run()` short-circuits with a
  message that reads like a *deployment* problem. That misdirection is half the
  cost — it points at the Hermes install rather than at a path constant.
- **Fix:** `home_path / "bin" / "hermes.exe"`. Worth also checking whether
  falling back to `hermes` on `PATH` is wanted, and whether any other module
  builds the same wrong path.
- **Blast radius:** everything that shells out to Hermes — Blueprint install,
  Agent create/delete, profile deploy, Skill deployment. On this machine that is
  the entire agent-provisioning surface.

### BUG-044 — a failed Blueprint install leaves the Section it created behind

- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-09-07, installing the `librarian` Blueprint on a clean install.
  The install failed at `blueprint_manager.py:166` (BUG-043), yet `GET /sections`
  afterwards shows **`Librarian`** present alongside the operator's own five.
- **Repro:** with BUG-043 unfixed, `POST /blueprints/librarian/install`. It
  returns 500; the Section survives.
- **Expected:** `install()`'s docstring states preconditions are checked first so
  that *"a refusal never leaves a partial install"*. Either the failure should be
  caught by a precondition, or the partial work should be rolled back.
- **Actual:** the guarantee holds only for *precondition* failures. This failure
  is **inside** the install, at `SectionManager().create(...)` — which creates
  the Section and then asks Hermes to create its Hub Agent. The Section write
  lands, the Hermes call fails, and nothing unwinds it.
- **Why it matters more than tidiness:** the natural next step is to retry the
  install, which now starts from a dirty state. And a Section is not inert —
  `SectionManager.create()` is documented as also creating a Hub Agent, so a
  partially-created Section may or may not have one, with nothing recording
  which.
- **Fix direction:** either extend the precondition check to prove Hermes is
  reachable *before* any write (it is already the first thing every agent step
  needs), or make `install()` unwind what it created on failure. The first is
  simpler and matches the docstring's stated intent.

### BUG-045 — an unhandled 500 reaches the browser as `TypeError: Failed to fetch`, hiding every server error from the UI

- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-09-07, deploying the `librarian` Blueprint. The operator saw
  only `TypeError: Failed to fetch` in the browser. The server had in fact
  answered **500** with a full traceback — none of which reached the UI.
- **Repro:** cause any endpoint to raise an unhandled exception (BUG-043 does it
  reliably: `POST /blueprints/librarian/install`) and call it from the frontend.
- **Expected:** the browser receives a 500 it can read, and the UI can surface
  something truthful ("the server failed", ideally with a reference).
- **Actual:** `fetch` rejects with `TypeError: Failed to fetch` — no status, no
  body. Indistinguishable from the backend being *down*, which is the damaging
  part: it sends you looking at the wrong layer.
- **Root cause, structural not incidental:** FastAPI mounts Starlette's
  `ServerErrorMiddleware` **outermost**, above user middleware. An exception
  propagating out of the app is turned into a 500 response *there* — above
  `CORSMiddleware` — so it is never processed on the way back out and carries no
  `Access-Control-Allow-Origin`. The browser then rejects it before the app sees
  it. Confirmed both ways in the traceback (`starlette/middleware/errors.py`
  frames wrap the app) and empirically: a **handled** 404 on the same origin
  *does* carry `Access-Control-Allow-Origin: http://localhost:5173`, so this is
  specific to unhandled exceptions, not to CORS config.
  `main.py` registers **zero** exception handlers.
- **Fix direction:** add a global `@app.exception_handler(Exception)` returning a
  JSON 500 through the normal response path, so CORS applies. That also gives one
  place to log the error id the UI can quote. Note this is already recorded as a
  standing constraint in `MEMORY.md` — it has bitten before and was never fixed.
- **Impact beyond this bug:** every future server-side failure is equally
  invisible in the UI. It cost real time here: the operator reported a fetch
  error, when the actual cause was a wrong executable path (BUG-043).
