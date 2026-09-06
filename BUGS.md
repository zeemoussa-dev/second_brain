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
| BUG-043 | `hermes.exe` is looked for one directory too deep, so every Hermes CLI operation fails on a correct install | Logic | Blocker | Closed | 2026-09-07 | `5f0f40e` |
| BUG-044 | A failed Blueprint install leaves the Section it created behind | Logic | Major | Open | 2026-09-07 | — |
| BUG-045 | An unhandled 500 reaches the browser as `TypeError: Failed to fetch`, hiding every server error from the UI | Logic | Major | Open | 2026-09-07 | — |
| BUG-046 | Blueprint install never asks which Section to install into — the Section is baked into the Blueprint and is not a parameter anywhere in the chain | Logic | Major | Open | 2026-09-07 | — |
| BUG-047 | The `librarian` Blueprint ships a whole Section covering three concerns; files and notes should be separate, independently installable Blueprints | Logic | Major | Open | 2026-09-07 | — |
| BUG-048 | `test_the_thread_mapping_still_matches_what_the_template_used_to_declare` asserts equality against LIVE machine state while its own docstring says subset, so it fails on every install that has not deployed all six thread-writing Skills | Logic | Minor | Open | 2026-09-07 | — |
| BUG-049 | `boot-status` reports `state: ready` with `checking_hermes: done` and `error: null` while `hermes_reachable` is `false`, and never re-checks — the app looks healthy while every agent chat is impossible | Logic | Major | Open | 2026-09-07 | — |
| BUG-050 | A Hermes WebSocket that closes mid-turn raises `ConnectionClosedError`, which the chat stream does not catch — the SSE response ends with HTTP 200 and an EMPTY body, and the dead session is never evicted so every later message fails the same way | Logic | Major | Open | 2026-09-07 | — |
| BUG-051 | The shipped `librarian` Blueprint hard-codes ANOTHER OPERATOR'S absolute vault path into all three Agent SOULs, so every fresh install's agents are pointed at a vault that is not theirs | Logic | Blocker | Open | 2026-09-07 | — |

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
- **Status:** Closed — fixed directly in `5f0f40e` at the operator's direction,
  outside the `/triage` story route, because the fix is one constant and the
  blocker was holding up a live install.
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
- **Fixed 2026-09-07 (`5f0f40e`).** Resolves `<home>/bin/hermes.exe`, falling
  back to `shutil.which("hermes")` when that layout is absent — asked
  deliberately, since only `home_path` is configuration and the subpath was our
  own assumption about the installer's layout. Verified live: `_hermes_exe()`
  returns `AppData\Local\hermesin\hermes.exe` and `hermes profile list`
  returns `ok=True`. No other module built the old path.

### BUG-044 — a failed Blueprint install leaves the Section it created behind

- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-09-07, installing the `librarian` Blueprint on a clean install.
  The install failed at `blueprint_manager.py:166` (BUG-043), yet `GET /sections`
  afterwards shows **`Librarian`** present alongside the operator's own five.
- **Repro:** with BUG-043 unfixed, `POST /blueprints/librarian/install`. It
  returns 500; the Section survives.
- **Proof it was the install and not the operator** (asked and checked, rather
  than assumed): the operator's own five Sections are all stamped **2026-09-05
  ~01:00**; `librarian` is stamped **2026-09-07 01:21:03**, matching
  `agent_sections.json`'s own mtime to the second. The backend process started
  01:18:13, and its log across that whole window contains **no `POST /sections`**
  — the single mutating request in it is the failed install. The Section's
  `icon`/`color` are also `null`, whereas a completed install would have set
  `database` / `#7c3aed` on the line immediately after `create()`; they are null
  precisely because the raise happened in between.
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
### BUG-046 — Blueprint install never asks which Section to install into

- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-09-07, installing the `librarian` Blueprint on a machine that
  already had five Sections (`Customers`, `Productivity`, `Sales`, `Core42`,
  `Products`). The install was never offered a choice — it went straight to
  minting a sixth Section named `Librarian`.
- **Repro:** `POST /blueprints/librarian/install` on an install with existing
  Sections, or click Install in the UI. No Section is asked for at any point.
- **Expected:** installing a Blueprint asks which Section its Agents should join
  — either an existing one or a new one — and defaults to the Blueprint's
  suggestion rather than imposing it.
- **Actual:** the target Section is fixed by the Blueprint file and cannot be
  overridden. The whole chain has no parameter for it:

  | Layer | Evidence |
  |---|---|
  | `Blueprint.json` | `"section": { "name": "Librarian", ... }` |
  | `blueprint.py:35` | `section_name: str` — a **required** field |
  | `blueprint_manager.py:166` | `SectionManager().create(blueprint.section_name)` |
  | `blueprints_router.py:47` | `install(blueprint_id, wire_peers: bool = True)` |

- **Root cause, and why it matters more than a missing prompt:** a Blueprint is
  currently modelled as *"a Section plus its Agents"*, not as *"a set of Agents"*.
  Because `section_name` is required, a Blueprint **cannot** be authored without
  bringing a Section along, and two Blueprints can never populate one Section.
  That single modelling choice is what forces the bundling in
  [[BUG-047]] — the granularity of a Blueprint is pinned to the granularity of a
  Section whether or not that suits the recipe.
- **Fix direction:** make the target Section an install-time argument
  (`install(blueprint_id, *, section_id: str | None = None, ...)`), demote
  `Blueprint.section` to a *suggested* Section used only when the operator asks
  for a new one, and have the UI ask. Once it is a parameter, several Blueprints
  can build into one Section and BUG-047 becomes authorable.
- **Related:** fixes BUG-047's precondition. Interacts with BUG-044 — today a
  failed install leaves behind a Section the operator never asked for in the
  first place.

### BUG-047 — the `librarian` Blueprint bundles three concerns into one all-or-nothing Section

- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-09-07, reviewing what `librarian` actually installs. Its own
  description names three concerns: *"files, notes and research"*.
- **What it ships:** one Section (`Librarian`) and three Agents —

  | Agent | Type | Skills |
  |---|---|---|
  | `files-manager` | producer | `capture-files`, `summarize-and-tag-files` |
  | `notes-manager` | producer | `capture-notes` |
  | `research-agent` | expert | `research-kb-writer` |

- **Expected:** files capture and notes capture are independent capabilities and
  should be **separate Blueprints**, each installable on its own into a Section
  the operator chooses. An operator who wants note capture and not file capture
  should be able to have exactly that.
- **Actual:** it is all-or-nothing. The three Agents arrive together, in a Section
  the Blueprint names, and there is no supported way to take one without the
  others short of hand-editing the Blueprint file — which then diverges from the
  shipped master on the next update.
- **Why this is structural, not just packaging:** `Blueprint.section_name` is a
  required field (`blueprint.py:35`), so a Blueprint always carries a Section and
  two Blueprints can never populate the same one. Splitting `librarian` into
  `files` and `notes` today would produce **two Sections**, which is worse than
  the bundle. **BUG-046 must be fixed first** — the split is only authorable once
  the target Section is an install-time argument.
- **Fix direction:** after BUG-046, split the library into at least a `files`
  Blueprint (`files-manager`) and a `notes` Blueprint (`notes-manager`), and
  decide deliberately where `research-agent` belongs — it is an `expert`, not a
  capture producer, and may warrant its own. Keep each Blueprint's peer routing
  snippet with its own Agent so `wire_peers` stays correct per-install.
- **Related:** blocked by [[BUG-046]].

### BUG-048 — a test asserts equality against live machine state while its own docstring says subset

- **Area:** Logic
- **Severity:** Minor
- **Status:** Open
- **Found:** 2026-09-07, running the suite after the `librarian` Blueprint
  install. Deploying four Skills took the suite from 3 failures to 1; this is the
  one that survives, and it will survive on any install short of a complete one.
- **The contradiction is inside the test itself.** Its docstring
  (`test_skill_writes_declaration.py:21`) states: *"Asserted as a SUBSET, not
  equality: the map legitimately grows as more Skills declare `writes:`, and
  pinning the whole map would fail every time coverage improves, which is the
  opposite of what this should reward."* The next line then asserts `==` against
  a hard-coded dict of six Actions.
- **Why it fails, and why that is the environment:** `build_section_access_map()`
  counts **only deployed** Skills — by design. This machine has
  `summarize-and-tag-files` deployed, giving `thread → Files →
  ["apply_file_review"]`; the other five Actions belong to Skills no profile here
  has. So the test is really asserting *"this machine has deployed every
  thread-writing Skill"*, which is a deployment fact, not a code property.
- **Expected:** the assertion matches the stated intent — the hard-coded mapping
  is a **subset** of the derived map, so improving coverage never breaks it and a
  partially-deployed install does not report a false failure.
- **Actual:** `assert ... == {...}` at `test_skill_writes_declaration.py:25`.
- **Fix direction:** assert per-section containment rather than dict equality, or
  build the map from a fixture set of Skills instead of live state. Prefer the
  second if the point is to guard the `allowed_callers` migration — that is a
  property of the declarations, and should not depend on what happens to be
  deployed on the machine running the suite.
- **Note for whoever picks this up:** this is the residue of a known class,
  already recorded in framework `MEMORY.md` — an empty access map on an
  undeployed machine is *correct*. Do not "fix" it by deploying more Skills.

### BUG-049 — `boot-status` reports ready while `hermes_reachable` is false, and never re-checks

- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-09-07, after the operator's first chat with the Notes Manager
  failed. The app had been reporting itself healthy the whole time.
- **Repro:** stop `hermes serve` (Hermes' backend server, port 9119), start the
  Second Brain backend, `GET /boot-status`:

      {"state":"ready", "stages":[{"id":"checking_hermes","status":"done"}, ...],
       "hermes_reachable":false, "error":null}

- **Expected:** a failed reachability check is visible — the stage does not read
  `done`, or `state` is not `ready`, or the UI surfaces the flag. Agent chat is
  the product's core function and it cannot work in this state.
- **Actual, two compounding faults** in `data_access/registry/loader.py`:
  1. **The check is computed and then ignored.** `_set_stage("checking_hermes",
     "done")` runs unconditionally after `_status["hermes_reachable"] =
     reachable`, so a failed check is indistinguishable from a passed one.
     `state` goes `ready` and `error` stays `null`.
  2. **It is a one-shot boot-time value that never refreshes.** Observed in both
     directions: it stayed `false` for minutes after Hermes came up, and only
     turned `true` on a full backend restart. A flag that lies in both directions
     is worse than no flag.
- **And nothing surfaces it.** `hermes_reachable` is declared in
  `frontend/src/features/boot/bootApiClient.ts:16` and referenced **nowhere else
  in the frontend** — the value crosses the wire and is dropped.
- **Fix direction:** fail (or warn) the stage when the check fails, re-check on a
  timer or on demand rather than once at boot, and render it — the operator
  should learn Hermes is down from the app, not from a chat that dies.

### BUG-050 — a dropped Hermes WebSocket ends the chat stream as HTTP 200 with an empty body

- **Area:** Logic
- **Severity:** Major
- **Status:** Open
- **Found:** 2026-09-07, chatting with `notes-manager`. Reproduced against
  `default` too, so it is not agent-specific.
- **Repro:** have the Hermes WS drop between session creation and the prompt
  (starting `hermes serve` after the backend has already tried to reach it does
  it), then `POST /agents/<id>/chat/stream`. Observed:

      HTTP 200  time=0.127s  bytes=0

  Server-side the traceback ends at
  `chat_session.py:129 send_prompt` -> `_call` -> `self._ws.send(...)` ->
  `websockets.exceptions.ConnectionClosedError: no close frame received or sent`.
- **Expected:** the same clean `{"type": "error", ...}` SSE frame the *other*
  Hermes failure already produces. When Hermes was simply down, the stream
  correctly yielded
  `{"type":"error","detail":"Hermes call failed (GET /, fetching session token):
  [WinError 10061] ..."}` — that path works.
- **Actual:** nothing at all. An empty 200 is the worst possible shape: the UI
  cannot tell it from an empty answer, and the operator sees a chat that returns
  silence.
- **Root cause — the wrapping is one line short.**
  `agent_chat_stream.stream_chat_turn:255` catches **`HermesUnavailableError`
  only**. `HermesChatSession.connect()` wraps its own failure (`except OSError`
  -> `HermesUnavailableError`), and `_recv_loop`'s `finally` wraps pending calls
  (`HermesUnavailableError("Hermes WS closed mid-call")`) — so the design clearly
  intends closed-mid-call to arrive as `HermesUnavailableError`. But `_call()`'s
  own `await self._ws.send(...)` sits outside any wrapper, and
  `ConnectionClosedError` is not an `OSError`, so that one path escapes uncaught,
  out of the generator, after the 200 headers have already been sent.
- **Second-order fault: the dead session is never evicted.**
  `chat_sessions.get_or_create_session` returns a cached session **without
  checking that its socket is still open** (`if session is not None: return
  session`). Eviction lives in the `except HermesUnavailableError` branch that
  never fires here, so the same dead WS is handed back to every later message —
  which is why this reproduced identically on every retry until the backend was
  restarted. `discard_session`'s own docstring names this exact scenario ("a
  socket that's already gone"), so the intent is there and only the trigger is
  missing.
- **Fix direction:** wrap the `send` in `_call` the way the rest of the class is
  wrapped, and have `get_or_create_session` verify the connection is open before
  handing a cached session back.

### BUG-051 — the shipped `librarian` Blueprint hard-codes another operator's vault path into every Agent SOUL

- **Area:** Logic
- **Severity:** Blocker
- **Status:** Open
- **Found:** 2026-09-07, on the first successful chat with `notes-manager` on
  this clean install. The agent reported success and the turn's own file-mutation
  verifier contradicted it:

      Captured to today's General Notes.
      WARNING File-mutation verifier: 1 file(s) were NOT modified this turn
        - `C:/Users/<other-operator>/OneDrive - <org>/.../second-brain/Work/Notes/2026-09-07/....md`
          [write_file] Failed to write file: mkdir: cannot create directory - Permission denied

  This machine's vault is not that path. The agent was writing into a **different
  operator's** vault location.
- **Root cause:** the Blueprint's own Agent SOULs carry a literal absolute path:

      blueprints/library/librarian/agents/notes-manager.soul.md:12
      blueprints/library/librarian/agents/files-manager.soul.md:14
      blueprints/library/librarian/agents/research-agent.soul.md:14

  each stating ``Vault path: `C:\Users\<other-operator>\OneDrive - <org>\...` ``.
  `install()` copies the SOUL verbatim into each Hermes profile, so **every**
  install gets it. Confirmed present in the deployed
  `profiles/notes-manager/SOUL.md` on this machine.
- **Expected:** a shipped master never contains one machine's paths. The SOUL
  should carry a placeholder resolved per-install from `vault_path` — the rule
  the repo already states: *"Never put a real vault path, mailbox, key or machine
  name in a repo file. Use `<OPERATOR_VAULT>` / `<operator>` placeholders —
  mixing instance detail into shared docs is what caused one install to act on
  another install's assumptions."*
- **Why Blocker:** the only reason this failed loudly here is that the foreign
  path is not writable on this machine. On any host where a similarly-named path
  *does* exist, the agent writes real notes into the wrong vault and reports
  success — silent data misplacement, far worse than an error. It also means
  every Agent this Blueprint installs is misconfigured from its first turn.
- **Also leaked, lower severity** (illustrative text, not live instructions, but
  the same rule): `skills/catalog/outlook/email-thread-capture/SKILL.md:84`,
  `skills/catalog/vault/summarize-and-tag-threads/SKILL.md:126`, and
  `skills/catalog/outlook/email-thread-capture/scripts/derive_noise_definition.py:36`
  each carry an operator-specific absolute path in an example.
- **Fix direction:** replace the SOUL line with a placeholder the installer
  substitutes from this install's configured `vault_path`, and scrub the three
  example paths. Worth a guard test that fails if any shipped master contains a
  literal `C:\Users\` path.
