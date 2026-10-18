---
id: REQ-SB-95-US-03-T05
title: The shipped runner Skill over loopback, honest refusal end-to-end, and the recorded unmet request
parent_story: REQ-SB-95-US-03
requirement_id: REQ-SB-95
type: backend
status: Done
gate: flagged
gate_reason: "ESC-074 Resolved — app/main.py was authorised for the seed call and nothing else; the starter now really installs on boot, verified on a disposable install on 127.0.0.1:8016. Flagged for the optional skim of the seven scope-internal judgement calls in the Implementation Log (unchanged from the first pass) — nothing is blocked."
phase: P2
depends_on: [REQ-SB-95-US-03-T01, REQ-SB-95-US-03-T03, REQ-SB-95-US-03-T04]
created: 2026-10-16
updated: 2026-10-18
---

# REQ-SB-95-US-03-T05 — The Runner Skill + "I Cannot Do That" as a Recorded Answer

## Parent Story

- Story: [[REQ-SB-95-US-03]] — `../UserStories/REQ-SB-95-US-03-published-catalogue-and-call-enforcement.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-95 *An Agent Can Only Do What the App Can Do — Operator Profile, Actions, Workflows, Entity Resolution*

---

## Objective

Give the agent its one door — a shipped runner Skill that posts to
`POST /actions/{action_id}/call` over loopback — and make "I cannot do that" a
real, recorded answer rather than a sentence.

---

## Starting State → End State

**Before / Inputs:**

- The gate, dispatch and confirmation are complete but reachable only from the
  UI and from a raw HTTP client.
- `business/core/skills/catalog/vault/vault-search/scripts/search_vault.py`
  already calls this app over loopback at
  `os.environ.get("SECOND_BRAIN_API_URL", "http://127.0.0.1:8001")`, and
  `vault-index/scripts/build_vault_index.py` POSTs `/vault-index/refresh` — the
  proven, shipped pattern this reuses. It is **not** the deleted inbound MCP
  surface.

**After / Outputs:**

- One shipped runner Skill under `business/core/skills/catalog/<tool>/<slug>/`
  (payload, never imported by the app — `ADR-019`) whose script:
  - posts the action id, the caller's own profile id and the inputs to
    `POST {SECOND_BRAIN_API_URL}/actions/{action_id}/call`;
  - relays a refusal verbatim, naming the cause, and never narrates an outcome
    that did not happen;
  - on an `awaiting_confirmation` response, reports the pending confirmation and
    stops;
  - on a `skill` grant, performs the named Skill in its own profile and reports
    the real outcome back.
- A shipped starter `report-unmet-request` Action (`ADR-032` allows shipped
  starters) so an unmet request lands as a row in the Action-call ledger.
- End-to-end honesty: an unknown id, a missing required input and a
  not-permitted caller each reach the operator as the framework's own refusal.

---

## Files to Modify

- `src/backend/app/business/core/skills/catalog/<tool>/<slug>/Skill.json` (new — the runner Skill definition; `<tool>/<slug>` chosen to match the existing catalogue's grouping convention)
- `src/backend/app/business/core/skills/catalog/<tool>/<slug>/scripts/call_action.py` (new — modelled on `search_vault.py`)
- `src/backend/app/business/core/actions/` starter-Action seed for `report-unmet-request` (the shipped-starter mechanism, mirroring how Master Templates ship)
- `src/backend/tests/test_action_runner_skill.py` (new)
- `src/backend/app/main.py` — **the seed call and nothing else** (added 2026-10-18 by the authorised scope extension below; `ESC-074` Resolved)

---

## Constraints

- Inherits from parent story.
- The runner is **payload**: the app must never import it (`ADR-019`). It is
  deployed into a Hermes profile like any other Skill.
- **No silent fallback.** The runner may not substitute a different action, a
  search, or a plausible narrative for a call it could not make — including
  when the backend is not running, which must surface as a connection failure,
  not a claimed success.
- The trust boundary is loopback and is stated honestly in `ADR-033`: the runner
  names its own profile id and the app believes it. Do not claim this sandboxes
  Hermes.
- `REQ-SB-33-US-01`'s honest-uncertainty instruction stays as it is.

---

## Tests

**Automated tests** — `src/backend/tests/test_action_runner_skill.py`, run with
`pytest tests/test_action_runner_skill.py` from `src/backend`. Import the
runner script by path as a payload script (the existing per-Skill
`scripts/tests/` pattern is the precedent) and point it at the real app through
a loopback-shaped transport.

1. `[REQ-SB-95-US-03-AC-03]` Drive the runner with an action id that is not in
   the catalogue; assert its output is the framework's own refusal naming the
   unknown id, that it reports inability rather than any outcome, and that a
   `refused:` ledger row exists.
2. `[REQ-SB-95-US-03-AC-04]` Drive it with a required input omitted; assert the
   output asks for that input by name and that no value was invented.
3. `[REQ-SB-95-US-03-AC-02]` Drive it with a valid `skill`-implementation call;
   assert it receives the single-use grant and performs the named Skill in its
   own profile, reporting the real outcome.
4. `[REQ-SB-95-US-03-AC-05]` Call the shipped `report-unmet-request` Action with
   an unmet-request text; assert a ledger row records the request text and that
   it is retrievable afterwards.
5. `[REQ-SB-95-US-03-AC-05]` Assert the runner surfaces a connection failure
   honestly when the app is unreachable, rather than reporting success.

**Manual verification steps:**

1. `[REQ-SB-95-US-03-AC-05]` With the backend running and the runner Skill
   deployed to a real Hermes profile, ask that agent in a real chat for
   something no catalogued Action covers. Confirm it states plainly that this
   app has no action for the request, does not invent one, does not promise it
   for later, does not claim it was done, and that a ledger row records the
   unmet request. Record the reply verbatim in the Implementation Log.
2. `[REQ-SB-95-US-03-AC-03]` In the same session, induce a call to a
   non-existent action and confirm the operator sees the honest refusal rather
   than a described outcome.

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] One shipped runner Skill, loopback, modelled on `search_vault.py`
- [x] Refusals relayed verbatim; no invented outcome on any path
- [x] `awaiting_confirmation` and `skill` grants handled correctly by the runner
- [x] Shipped `report-unmet-request` starter Action; unmet requests recorded —
      **seeded on boot 2026-10-18 (`ESC-074` Resolved); verified on a real boot**
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- A reviewable capability-request backlog UI (story Non-Goals).
- Any general inbound Hermes→app API surface beyond this one route.
- Workflow runs — `REQ-SB-95-US-04-T05`.

---

## Context / Notes

`architecture.md` → **§The Action Call Gate** ("The agent's only door is one
shipped runner Skill") and **§Confirmation and the Action-Call Ledger** (the
`report-unmet-request` starter). `ADR-033` records the loopback precedent with
the exact two shipped scripts to model this on — read both before writing.

---

## Implementation Log

**2026-10-18 — built and verified; `Blocked` on one out-of-scope line
(`ESC-074`).** Suite **525 → 538 passed, 0 failed** (the task's own baseline at
`6fce391` was **511**; another session landed `SPRINT-091`'s `T01` plus three
more commits mid-task, moving HEAD to `c826512` and the upstream baseline to
525 — re-measured, not assumed). Commits: `af54a4c` (the missing UI feature
key, `ESC-071`), `ce38963` (the shipped starter + its seed), `199d2dc` (the
runner Skill + 12 AC-tagged tests).

### What shipped

**The runner Skill — `business/core/skills/catalog/actions/call-action/`.**
`SKILL.md` + `scripts/call_action.py`: stdlib-only payload, deployed into a
Hermes profile, never imported by the app (`ADR-019`). It POSTs
`{"caller_agent_id", "inputs", "confirmed_call_id"}` to
`{SECOND_BRAIN_API_URL}/actions/{action_id}/call`, the exact body the catalogue
block already tells agents to send (`T01`), and branches on **`accepted`** and
nothing else — the field `T02` made separate from `outcome` precisely so a
runner cannot read a new outcome word as success. Its answers:

| What the app said | What the runner says | Exit |
|---|---|---|
| `accepted: false` | `REFUSED BY THE APP (<outcome>, call <id>)` + the refusal **verbatim** + "do not substitute another action" | 2 |
| `awaiting_confirmation` | `WAITING FOR THE OPERATOR` + the call id + "do not retry" — and it stops | 2 |
| `performed` | `PERFORMED` + the route's own real result | 0 |
| `pointed_at` | `RECORDED, NOT PERFORMED` + the screen the operator does it on | 0 |
| `authorised` | runs the granted Skill **here**, reports its real exit status and its own words | 0 / 1 |
| `failed` | `THE APP TRIED AND FAILED` — the operation did not happen | 1 |
| anything else | names it and refuses to interpret it | 1 |
| unreachable | `NOTHING WAS PERFORMED: ... could not be reached at <url>` | 1 |

It names itself by the profile it is deployed in — `<home>/profiles/<id>/skills/
<tool>/<slug>/` read off its own `__file__`, with `--caller` and
`HERMES_PROFILE_ID` ahead of it — and **refuses to call at all** when it cannot
tell, because the app believes the id it is given (`ADR-033`'s loopback trust
boundary) and a guessed one would record a call nobody made.

**The shipped starter — `business/core/actions/starters/report-unmet-request/
Action.json`** plus `shipped_starters.py` and
`ActionManager.seed_shipped_starters()`, mirroring
`TemplateManager.seed_shipped_masters()` including its one hard rule (an id this
install already has is **never** overwritten — the seed is meant to run on every
boot and would otherwise revert the operator's edit on every restart). The
Action's implementation is `ui` → `/settings/actions`: the app genuinely cannot
do anything about a capability it does not have, so it performs nothing and the
record is the product. `allowed_callers: ["*"]` — an agent not told it exists
cannot use it. Required input `request` ("their own words — not a paraphrase and
not your guess at which action they meant"), optional `why_no_action_matched`.

### AC verification

Automated: `tests/test_action_runner_skill.py`, 12 tests, run with
`pytest tests/test_action_runner_skill.py` from `src/backend`. The shipped
script is loaded **by path** and driven through its real `main()` over a real
command line; `urllib.request.urlopen` is replaced by one that takes the very
`Request` the runner built, asserts the POST shape, and hands it to `TestClient`
— `httpx.ASGITransport(app=app)`, in process. So the gate, the dispatch and the
ledger are real, no socket is opened, and a refusal arrives as a real
`HTTPError` with its body.

| AC | Step | Observed |
|---|---|---|
| `REQ-SB-95-US-03-AC-03` | unknown action id through the runner | `exit 2`, `REFUSED BY THE APP (refused:unknown_action, call <id>)`, `"there is no action 'send-the-invoice' in this install's catalogue"` relayed verbatim, none of `PERFORMED`/`AUTHORISED`/`RECORDED` present, ledger row `refused:unknown_action` naming the id. **Pass** |
| `REQ-SB-95-US-03-AC-03` | a caller not in `allowed_callers` | `exit 2`, `refused:caller_not_permitted`, `"agent 'someone-else' may not run action 'capture-this-thread'"`, ledger row. **Pass** |
| `REQ-SB-95-US-03-AC-04` | a required input omitted | `exit 2`, `refused:missing_required_input`, names `'folder'` and "ask for it by name — nothing is guessed or defaulted in its place"; the sent inputs and the ledger row both hold exactly `{"urgent": "true"}` and the string `folder` appears in neither. **Pass** |
| `REQ-SB-95-US-03-AC-02` | a valid `skill`-implementation call | `exit 0`, `AUTHORISED`, the grant received, the Skill **really run** in a throwaway profile under `tmp_path` in the deployed flat shape, its own stdout (`filed thread AAMk-0042`) relayed; the Skill's side-effect file proves it got the validated inputs on **both** stdin and `SECOND_BRAIN_ACTION_INPUTS`, and the call id; ledger `authorised`. The runner derived its own caller id from its deployed path and the app accepted it. **Pass** |
| `REQ-SB-95-US-03-AC-02` | a granted Skill that fails | `exit 1`, `RAN AND FAILED (exit 3)` with the Skill's own stderr, the word `successfully` absent. **Pass** |
| `REQ-SB-95-US-03-AC-05` | the shipped starter called with an unmet request | `exit 0`, `RECORDED, NOT PERFORMED`, "claiming it was done would be false"; the ledger row holds the operator's words under `inputs.request`, outcome `pointed_at`, and is **retrievable afterwards** through `action_calls.read_call_json()` by the id it reported. **Pass** |
| `REQ-SB-95-US-03-AC-05` | the app unreachable | `exit 1`, `NOTHING WAS PERFORMED: ... could not be reached at <url>`, "do not report the action as done", "do not attempt it another way"; **no ledger row at all**, because no call was made. **Pass** |
| `REQ-SB-95-US-03-AC-06` | `awaiting_confirmation`, then the confirmed re-call | first call: `WAITING FOR THE OPERATOR`, nothing performed, the call id named, and **exactly one** HTTP call made (it stopped rather than retrying); after `POST /actions/calls/<id>/confirm`, the re-call with `--confirmed-call-id` is accepted and leaves the second row joined by `granted_by_call_id`. `T04` owns `AC-06`; this is the runner's half of it. **Pass** |

**Manual steps.** Performed against a **disposable install on
`127.0.0.1:8015`** — its own vault, data path and Hermes home under the session
scratchpad — with the **shipped script copied into a profile in the deployed
flat shape** and run as a real subprocess over a real loopback socket. The
operator's `:8001` was never called (`T03` used `:8013`, `T04` `:8014`).
Verbatim, as the operator would read them:

1. `[REQ-SB-95-US-03-AC-03]` an action id nobody has —
   `python call_action.py book-the-meeting --input when=Tuesday`:

   ```
   REFUSED BY THE APP (refused:unknown_action, call 9457097e20794e2d835e6eed3412afb7). NOTHING WAS PERFORMED.
   there is no action 'book-the-meeting' in this install's catalogue, so it cannot be called
   Relay this to the operator as it is written. Do not substitute another action, do not do it another way, and do not describe an outcome that did not happen.
   [exit 2]
   ```

2. `[REQ-SB-95-US-03-AC-04]` the required input omitted:

   ```
   REFUSED BY THE APP (refused:missing_required_input, call daa9ca0c462042bcbadf49f639936245). NOTHING WAS PERFORMED.
   action 'report-unmet-request' requires 'request', which this call did not supply; ask for it by name -- nothing is guessed or defaulted in its place
   ```

3. `[REQ-SB-95-US-03-AC-05]` something no catalogued Action covers:

   ```
   RECORDED, NOT PERFORMED (call b05e64ed14f74eb0b354ef80a38fcfc7).
   action 'report-unmet-request' is something only the operator can do, on this app's '/settings/actions' screen. Nothing was performed -- tell the operator to go there.
   The operator does this themselves at /settings/actions. Say so plainly; claiming it was done would be false.
   [exit 0]
   ```

   and on disk, `<DATA_PATH>/data/ActionCalls/b05e64…json`:

   ```json
   { "action_id": "report-unmet-request", "caller_agent_id": "manual-test-agent",
     "inputs": { "request": "book the Tuesday refinery meeting into my Outlook calendar",
                 "why_no_action_matched": "the catalogue has one action and it is this one" },
     "outcome": "pointed_at", "grant": null }
   ```

   `caller_agent_id` is the profile the runner worked out from its own deployed
   path, over the wire, with no `--caller` passed.

4. `[REQ-SB-95-US-03-AC-05]` the backend stopped, same command:

   ```
   NOTHING WAS PERFORMED: Second Brain could not be reached at http://127.0.0.1:8015 (<urlopen error [WinError 10061] No connection could be made because the target machine actively refused it>). Tell the operator the app is not running -- do not report the action as done and do not attempt it another way.
   [exit 1]
   ```

**What the manual steps did NOT cover, stated plainly.** The task's manual steps
are written as a real chat with a real agent in a real Hermes profile. That half
was not performed: deploying this Skill into one of the operator's 41 live
profiles is the exact accident `tests/conftest.py` exists to prevent, and the
disposable install has no Hermes gateway or model keys. What was run instead is
the shipped script itself over a real socket — which is *literally* the text the
agent would relay, since the runner's output is the agent's source of truth
about what happened. The model-side clauses ("states plainly", "does not invent
an action") rest on that text plus `T01`'s published block, both of which are
recorded above verbatim. Recorded as an assumption for human spot-check, not as
a pass.

### Where writes, subprocesses and outbound calls landed

Measured before the suite was trusted, behind a plugin wrapping `Path.write_text
/write_bytes/open/mkdir/unlink`, `builtins.open` (write modes), `os.makedirs/
remove/system`, `shutil.rmtree/copy/copyfile/copytree`, `socket.socket.connect/
connect_ex`, `httpx`'s **real** `HTTPTransport`/`AsyncHTTPTransport`,
`urllib.request.urlopen` and `subprocess.Popen.__init__`, classifying every
target against the real vault, data path and Hermes home:

- **this file alone (12 tests): 0 writes** anywhere under the vault, the data
  path or the Hermes home; **0** real httpx requests; **0** `urlopen` calls (the
  loopback transport is in process); 3 subprocesses — one pre-existing
  `git rev-parse HEAD` from the version module, and the **two deliberate ones**,
  both `…/.venv/Scripts/python.exe <pytest tmp>/…/capture-the-thread/capture.py`
  inside pytest's own tmp tree;
- **the whole 538-test suite:** 7150 write calls seen, **9** touching a
  protected root — all of them `Path.mkdir` on the data-path root itself, which
  already exists and is pre-existing (0 of them come from this file); **0**
  connects to `:8001`, `:8088`, `:8090` or `:5173` (185 connects, all ephemeral
  local ports from anyio's own portal); one real httpx request, to
  `127.0.0.1:9119`, which is a pre-existing unreachable-port test; the remaining
  subprocesses are the plugin/marketplace suites' `git` calls in tmp dirs.

### Judgement calls (in scope — for human spot-check, not escalations)

1. **The Skill definition is `SKILL.md`, not the `Skill.json` this task's
   `## Files to Modify` names.** There is no such thing as a `Skill.json` in
   this codebase: `data_access/skills.py` finds a Skill by `<tool>/<slug>/
   SKILL.md` and a folder without one is invisible to `list_skill_ids()`, so a
   `Skill.json` would have shipped a Skill nothing could deploy. Same artefact,
   the catalogue's real name for it.
2. **Tool folder `actions/`, slug `call-action`** — a new Tool folder, which
   `list_categories()` picks up by existing. The catalogue's README says the
   Tool is "the capability domain the Skill acts through", and this one acts
   through the app's Action API, not the vault.
3. **`shipped_starters.py` lives in the business package, not in
   `data_access/actions.py`.** Every raw read of *install* data still goes
   through `data_access`; this reads bundled **source** shipped beside the
   Manager, the same category as `action.py`'s own `UI_FEATURE_KEYS` constant.
   `data_access/templates.py` holds the equivalent reader for Master Templates,
   so moving these two functions there is a one-line change a human may prefer —
   it was kept here because `data_access/` is outside this task's scope. Noted
   in the module's own docstring.
4. **A granted Skill receives its validated inputs as JSON on stdin AND in
   `SECOND_BRAIN_ACTION_INPUTS`** (`SECOND_BRAIN_ACTION_CALL_ID` beside it).
   `ADR-033` says the runner performs the Skill but nothing said how a Skill
   receives Action inputs, and no such contract existed — every deployed Skill
   today is agent-mediated with its own hand-written CLI. Two channels rather
   than invented `--flag` names, because a flag name would be a guess about a
   script this runner has never seen. Documented in the Skill's own `SKILL.md`
   and recorded in `MEMORY.md` as a pattern.
5. **Which script runs a granted Skill is read from that Skill's own
   `SKILL.md`** (the `python …<name>.py` command `test_skill_command_paths.py`
   already pins against what the deploy writes), falling back to the single
   `.py` file when a Skill has exactly one — and **refusing to pick** when it is
   ambiguous, reporting that nothing was performed. A guessed entry point is the
   silent fallback this whole task exists to prevent.
6. **The runner cannot tell the app that a granted Skill finished.**
   `consume_single_use_grant(reported_outcome=…)` was built by `T03` for exactly
   that, but no route exposes it (`actions_router.py` and
   `action_invocation.py` are both outside this scope), so a performed grant
   leaves its ledger row at `authorised` and the operator learns the real
   outcome from the agent. Not a defect of anything built here; filed as an open
   follow-up in the sprint retro.
7. **`confirmed_call_id` is NOT published into the agents' SOUL block** —
   decided by the orchestrator before this task started, and the task holds to
   it: the refusal sentence already carries the whole instruction at the moment
   the agent needs it, so an agent discovers confirmation by being refused once
   rather than by carrying standing text it will rarely use. `agent_manager.py`
   was not touched. No case was found where discover-on-refusal fails: the
   `awaiting_confirmation` refusal names the call id, the action, the inputs to
   repeat and the field to send.

### Escalations

- **`ESC-074` (Open) — this task is `Blocked` on it.** The starter's seed is
  built, tested and committed; the boot call that runs it lives in
  `app/main.py`, five lines below the Master Template seed it mirrors, and that
  file is in no task's `## Files to Modify`. Three in-scope alternatives were
  worked through and rejected — all of them either break a `Done` task's test
  (`test_an_agent_permitted_to_call_nothing_carries_no_block_at_all`, because
  the starter is `["*"]` and a read-time composition bypasses the store that
  test replaces) or put an Action in the gate that no agent is told about and no
  screen lists. The escalation carries the exact five lines to authorise.
- **`ESC-071` (Resolved here)** — `/settings/actions` was missing from
  `UI_FEATURE_KEYS`; that escalation's own option (b) was "fold it into
  `REQ-SB-95-US-03`", `action.py` is inside this task's scoped directory, and
  the starter needs the key. Added in `af54a4c`. The deeper question — a
  hand-maintained mirror of another build's route table drifts by construction —
  is **not** solved and is carried into the retro as a follow-up.

---

## Scope extension — 2026-10-18 (unblocks `ESC-074`)

**Added to `## Files to Modify`:** `src/backend/app/main.py` — the boot call only.

`seed_shipped_starters()` is built, tested and committed, and nothing calls it. The
call belongs beside the Master Template seed in the startup lifespan, which is in no
task's file list. The three in-scope alternatives were worked through and correctly
rejected: composing on read breaks a `Done` task's test, and `get_by_id`-only
composition would put an Action in the gate that no agent is told about and no screen
lists.

Scope is **the seed call and nothing else** in that file. Then finish the task's own
verification and draft the sprint retrospective — `SPRINT-088` closes with you.

This is the fifth escalation of one shape in two sprints, and the generator has now
been fixed rather than the instance: `.claude/agents/decomposer.md` carries a standing
rule to name the switch-on site, and framework `MEMORY.md` records why.

---

## Implementation Log — second pass, 2026-10-18 (`ESC-074` Resolved; task `Done`)

**The one authorised line, and nothing else.** `dcfa14b` adds `ActionManager` to
`app/main.py`'s imports and the five-line seed call to the startup lifespan,
immediately after the Master Template seed it mirrors. The diff is 15 added
lines and 0 removed; no other line of that file was touched, and nothing else in
the repo changed in that commit.

```python
    try:
        starters = ActionManager().seed_shipped_starters()
        if starters["seeded"]:
            print(f"[startup] seeded starter Actions: {', '.join(starters['seeded'])}")
    except Exception as exc:
        print(f"[startup] ERROR: could not seed starter Actions: {exc!r}")
```

The `try/except` is not decoration: it is the same shape as the Master Template
seed above it and for the same reason — a malformed shipped starter is a build
defect, and refusing to boot would hide it behind a dead port the operator
cannot reach to be told.

### Observed outcome of the seeding, once wired

Verified on a **disposable install on `127.0.0.1:8016`** — its own vault, data
path and a Hermes home pointed at a directory that does not exist, all under the
session scratchpad. The operator's `:8001` was never called and was still
listening, untouched, afterwards (`T03` used `:8013`, `T04` `:8014`, this task's
first pass `:8015`).

1. **First boot of an install that had never seen the starter.** stdout:

   ```
   [startup] seeded Master Templates: file, meeting, meeting-series, note, research-kb-doc, thread
   [startup] seeded starter Actions: report-unmet-request
   INFO:     Application startup complete.
   ```

   `GET /actions` on that install then returned exactly one row —
   `{"id":"report-unmet-request","implementation_kind":"ui","status":"resolves"}` —
   with the shipped description. **Pass.** This is the half `ESC-074` said was
   true of the mechanism and not of the product; it is now true of the product.

2. **The agent's own door, end to end, on that same fresh install, with no
   manual seeding anywhere.** The shipped `scripts/call_action.py` was copied
   into a profile in the deployed flat shape
   (`<home>/profiles/disposable-test-agent/skills/actions/call-action/`) and run
   as a real subprocess over a real loopback socket, deriving its own caller id
   from its deployed path with no `--caller` passed:

   ```
   RECORDED, NOT PERFORMED (call c4f23f7314834381a470d108e1f91af2).
   action 'report-unmet-request' is something only the operator can do, on this app's '/settings/actions' screen. Nothing was performed -- tell the operator to go there.
   The operator does this themselves at /settings/actions. Say so plainly; claiming it was done would be false.
   [exit 0]
   ```

   and `<DATA_PATH>/data/ActionCalls/c4f23f73….json` on disk:

   ```json
   { "action_id": "report-unmet-request", "caller_agent_id": "disposable-test-agent",
     "inputs": { "request": "book the Tuesday refinery meeting into my Outlook calendar",
                 "why_no_action_matched": "the catalogue has one action and it is this one" },
     "outcome": "pointed_at", "grant": null, "refusal": null }
   ```

   **Pass.** The operator's own words are in the ledger, on an install whose only
   contact with the starter was starting up.

3. **The seed never overwrites — proved across a restart, not asserted.** The
   seeded Action's `description` was hand-edited on disk to
   `"OPERATOR EDITED THIS DESCRIPTION BY HAND"` and the backend restarted. The
   second boot printed **no** `seeded starter Actions:` line at all (nothing was
   seeded, the id was kept) and the hand edit was still there afterwards.
   **Pass.** This is the one hard rule the seed inherits from
   `seed_shipped_masters()`, and the reason a boot-time seed is safe to run on
   every restart.

### AC verification — final state

The first pass's twelve AC-tagged automated tests are unchanged and still pass;
the table in the first Implementation Log above stands as written. What changed
is only `AC-05`'s product half, which the three observations above close.

| AC | Final state |
|---|---|
| `REQ-SB-95-US-03-AC-02` | **Verified.** A valid `skill` call receives the grant, performs the named Skill in its own profile, and reports its real exit status and words; a granted Skill that fails is reported as failed. Unchanged from the first pass. |
| `REQ-SB-95-US-03-AC-03` | **Verified.** An unknown id and a not-permitted caller each reach the operator as the framework's own refusal, verbatim, with a `refused:` ledger row and no narrated outcome. Unchanged from the first pass. |
| `REQ-SB-95-US-03-AC-04` | **Verified.** A missing required input is refused by name, nothing is guessed, and the string never appears in the sent inputs or in the ledger row. Unchanged from the first pass. |
| `REQ-SB-95-US-03-AC-05` | **Verified, and now true of the product as well as the mechanism.** The starter installs itself on first boot, an unmet request lands in the ledger in the operator's own words and is retrievable afterwards, and an unreachable app surfaces as a connection failure with no ledger row, because no call was made. |

`AC-01`, `AC-06`, `AC-07` and `AC-08` belong to `T01`/`T02`/`T04` and were
verified there; `T05` carries the runner's half of `AC-06` and it passed in the
first pass.

**What is still NOT covered, restated plainly so it is not read as a pass.** The
task's manual steps are written as a real chat with a real agent in a real
Hermes profile, and that half was not performed in either pass — deploying this
Skill into one of the operator's 41 live profiles is the exact accident
`tests/conftest.py` exists to prevent, and no disposable install has a Hermes
gateway or model keys. What was run instead is the shipped script itself over a
real socket, which is literally the text the agent would relay. Recorded as an
assumption for human spot-check.

### Test numbers

- **Baseline measured, not assumed:** `538 passed, 0 failed` at `fe4b0c1`, taken
  immediately before the edit. (The task's first pass measured 538 at `c826512`;
  `f21f054` and `fe4b0c1` are docs-only and moved nothing.)
- **After the edit, same HEAD:** `538 passed, 0 failed` — twice, once plain and
  once behind the side-effect interceptor.
- **Final run:** `548 passed, 0 failed`. The +10 is **not this change**: the
  concurrent `SPRINT-091` session landed `e373391`
  (*"a failed toolsets read is not 'nothing is enabled'"*) with ten tests of its
  own mid-run. Neither known flake fired in any of the four runs.

This task adds no test of its own in this pass, by design: **no test in the
suite enters `app.main`'s lifespan** (verified by search — the only mention is
`test_plugin_host.py`'s own note that it deliberately builds a bare FastAPI app
instead), so a test asserting the boot call would have to construct the lifespan
specially and would prove the test's own wiring rather than the product's. The
boot is verified where it actually happens, on a real `uvicorn` start.

### Where writes, subprocesses and outbound calls landed

Re-measured with the seed live, behind the same plugin as the first pass
(`Path.write_text/write_bytes/open/mkdir/unlink`, `builtins.open` in write
modes, `os.makedirs/remove/system`, `shutil.rmtree/copy/copyfile/copytree`,
`socket.socket.connect/connect_ex`, the **real** `httpx.HTTPTransport`/
`AsyncHTTPTransport`, `urllib.request.urlopen`, `subprocess.Popen.__init__`),
classifying every target against the real vault, data path and Hermes home:

- 7148 write calls seen; **9** touching a protected root — all of them
  `Path.mkdir` on the data-path root itself, which already exists and is
  pre-existing. Identical to the first pass's 9.
- 185 socket connects, **0** to `:8001`, `:8088`, `:8090` or `:5173`.
- **1** real httpx request, to `127.0.0.1:9119` — the pre-existing
  unreachable-port test. **0** `urlopen` calls.
- 78 subprocesses, all `git` in pytest tmp trees (the plugin/marketplace suites)
  plus the version module's own `git rev-parse HEAD`.

`tests/conftest.py`'s Hermes sandbox was not weakened, bypassed or
special-cased, and the profile used in the live step was created under the
disposable install's own non-existent-by-default Hermes home, never the
operator's.

### Judgement calls added by this pass

None. The seven recorded in the first pass stand unchanged — in particular
number 6 (`consume_single_use_grant(reported_outcome=…)` is built and no route
exposes it, so a performed grant's ledger row still reads `authorised`), which
is carried into the sprint retro as an open follow-up rather than silently
fixed, because both files that would expose it are outside this task's scope.

### Escalations

- **`ESC-074` — Resolved.** Authorised as a scope extension; the resolving
  artefact is this task plus commit `dcfa14b`. The three in-scope alternatives
  recorded in the first pass were correctly rejected and none of them was taken.
- **`ESC-071` — Resolved** in the first pass (`af54a4c`). The drift *mechanism*
  it exposed is untouched and is the first open follow-up in the sprint retro.
- **Nothing new was escalated by this pass.**
