# Learnings

Append-only cross-sprint index of patterns and antipatterns harvested from sprint
retrospectives. Populated by the **human** from the coder's drafted retro. Read
this at the start of every new sprint.

<!-- Entry format:
## YYYY-MM-DD — SPRINT-NNN
### Patterns (do more of this)
- Pattern name — context and why it worked

### Antipatterns (avoid this)
- Antipattern name — context and why it hurt

### Sizing calibration
- Estimated vs. actual — takeaway for future sprint sizing
-->

## 2026-08-12 — SPRINT-018

### Patterns (do more of this)

- **In-process monkeypatch of a real, already-loaded dependency to induce a
  failure condition, instead of editing a file outside the task's own
  scope** — when a task's Tests section names an out-of-scope-file
  technique as one *example* way to induce a real failure (not a locked-AC
  requirement of that specific mechanism), a throwaway script that loads
  the real dependency, monkeypatches just the failing call in-process, and
  invokes the real, unmodified production function directly achieves the
  same genuine verification with zero file edits and zero revert step.
  Found live, `REQ-SB-33-US-01-T01`.
- **Frame a "does the model fabricate from general training knowledge"
  test around a real, in-vault entity, not a wholly fictitious one** —
  asking about real-world facts of an entity that genuinely exists in the
  vault (but whose specific fact was never actually retrieved by any tool
  call) is a sharper test of whether a grounding instruction actually
  works than an obviously-irrelevant question, which a model might decline
  for unrelated scope reasons regardless of any grounding instruction.
  Found live, `REQ-SB-33-US-01-T01`.
- **Cross-check a model's answer against an independent, direct call to
  the same tool function** (not through the agent) to turn "the reply
  sounds plausible" into "the reply is byte-for-byte the real tool's own
  output" — a stronger regression-guard confirmation than eyeballing the
  reply alone. Found live, `REQ-SB-33-US-01-T01`.

### Antipatterns (avoid this)

- **Trusting a long-running real-Provider chat call is "just slow" without
  a control check** — left running past this project's own documented
  Compass-latency precedent without independently confirming the server
  was still alive via a trivial, unrelated `GET`. A quick control probe
  against the same server, in parallel with any single real-Provider call
  expected to take more than ~30-60s, catches a genuine hang sooner
  instead of waiting on an indefinitely stuck background call. Found live,
  `REQ-SB-33-US-01-T01` — root cause tracked as `BUG-007`
  (`graph.py::_call_model` is a synchronous node with a blocking Provider
  call inside an otherwise-async graph, in apparent tension with this
  project's own standing async-graph-node Constraint).

### Sizing calibration

- **Estimated:** ~1 task, XS — **Actual:** 1 task, XS (one prompt-content
  edit to one function; verification, not code volume, was the real cost)
  — **Takeaway:** the sizing estimate was accurate for build effort, but
  didn't capture real-Provider-call latency variance during live
  verification. Worth naming explicitly in future XS-sized prompt-only
  stories that still require several real Provider round-trips to verify.

## 2026-08-12 — SPRINT-019

### Patterns (do more of this)

- **When a task's own code sample is later found to disagree with a real
  live HTTP call, treat the live call as ground truth and correct the
  code in-scope, not the other way around** — a task's spec'd
  `httpx.get()` call (no `follow_redirects`) disagreed with the real
  target endpoint's own `307`→`406` redirect chain. The fix stayed
  entirely inside the task's own file, required no new
  dependency/interface/ADR, and was caught early specifically because a
  backend-layer smoke check ran *before* the frontend task started.
  Found live, `REQ-SB-31-US-01-T02`.
- **When a locked AC's own wording implies "the exact same underlying
  condition, shown two different ways on the same page," induce both
  real conditions together in one combined edit/revert cycle** rather
  than as two fully separate live passes — halves the number of real
  backend-reload/API-round-trip cycles needed. Found live,
  `REQ-SB-31-US-01-T04`.
- **Backend-layer-first live verification** (hit the new endpoint
  directly before writing any frontend code against it) keeps root-cause
  debugging at the layer where the bug actually lives, instead of
  surfacing as a confusing frontend-layer mystery later. Reconfirmed,
  `SPRINT-019`.
- **The specific-PID-kill-and-restart protocol generalizes** beyond its
  original literal "orphaned process" failure mode — it also recovered a
  `--reload` server serving stale code with a fully alive (not orphaned)
  process tree. Reconfirmed, `SPRINT-019`.

### Antipatterns (avoid this)

- **Recording a live-observed HTTP status-code finding ("confirmed
  live") without also recording which client/method produced it** — a
  redirecting endpoint can genuinely show different status codes to a
  redirect-following client (browser/PowerShell) vs. a raw `httpx.get()`
  (redirect-following off by default), and the same "ground truth" claim
  can be simultaneously true and misleading to a later reader depending
  on tooling defaults never written down. Found live,
  `REQ-SB-31-US-01-T02`.

### Sizing calibration

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — accurate. The
  estimate's own reasoning (only the frontend task carries real UI
  surface and most of the story's ACs) held up almost exactly; that
  task's live verification (4 real state inductions, 4 screenshots, one
  live bug found and fixed) was the real cost center, as predicted.

## 2026-08-12 — SPRINT-020

### Patterns (do more of this)

- **Verify `onChange`/`onBlur`-driven React commit handlers via
  Fiber-props direct-invoke by default in a headless-Chrome-via-CDP
  session, not native DOM `focus()`/`blur()` calls** — even a real
  `.focus()`/`.blur()` DOM-API call pair (which genuinely changes
  `document.activeElement`) did not reliably deliver the native
  `focusout` bubbling event React's `onBlur` prop depends on in this
  headless environment. Reading the real handler off
  `element[Object.keys(element).find(k =>
  k.startsWith('__reactProps$'))].onBlur` and invoking it directly,
  confirming a real network request fired, is faster and more reliable
  than debugging synthetic-event delivery first. Extends the existing
  `onClick`-on-`disabled`-button precedent (`REQ-SB-18-US-01-T07`) to
  `onBlur`-on-commit-input; likely generalizes to other React synthetic
  event types in this same harness. Found live, `REQ-SB-20-US-01-T06`.
- **Run a task's own illustrative example test data live before trusting
  it, even when it looks obviously correct on inspection** — a
  deterministic keyword-substring-match algorithm is simple enough that
  an example string can *look* like it should match while not actually
  being a literal substring (singular vs. plural, an apostrophe-s
  changing the character sequence). Cheap to fix, but only surfaces by
  actually running it. Found live, `REQ-SB-20-US-01-T02`/`T05`.
- **"Compose the new change around the REAL current file, never
  overwrite it with the stale sample"** generalized cleanly a second
  time (first found `REQ-SB-26-US-01-T03`) — reading the real current
  file before applying any diff caught a genuinely load-bearing
  divergence (a routing tool-call had to be intercepted before the
  graph's own generic tool-execution node, not after). Reconfirmed,
  `REQ-SB-20-US-01-T05`.

### Antipatterns (avoid this)

- **Assuming a task file's own "Before" code sample still matches the
  real current file's shape once 2+ sibling stories may have landed
  additive changes to the same shared file in between** — this is now
  the second time this exact class of drift required reconciliation
  against reality, both times on `graph.py` specifically, this project's
  most actively-extended shared file. Always re-read the real current
  file immediately before applying any task's own literal code block to
  it. Found live, `REQ-SB-20-US-01-T05`.

### Sizing calibration

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — accurate. `T05`
  (the graph node) was the heaviest by a wide margin, not in task count
  but in the real-file reconciliation needed against three sibling
  stories' intervening changes.

## 2026-08-12 — SPRINT-021

### Patterns (do more of this)

- **A "harmless, no cleanup needed" throwaway test artefact is only
  harmless relative to the code that exists *at the time the smoke
  check runs*** — re-check that assumption whenever a later task adds
  new code that iterates/renders the same store unconditionally, and
  either prune the artefact or make the new code degrade gracefully
  (ideally both). Found live, `REQ-SB-21-US-01-T07` (a stale
  `pending_approval_id` from `T01`'s own smoke check became a real
  unhandled-rejection defect once `T07` started resolving every
  proposal's live status).
- **When a real background/scheduled pipeline call is part of a task's
  own mandated live verification, assume multi-minute latency up front
  and background the shell call with unbuffered output from the
  start**, rather than discovering the timeout mid-verification and
  having to re-run. Found live, `REQ-SB-21-US-01` (a real capture run
  took 1.5-5 minutes, well past the shell's 2-minute default timeout).
- **A task's own `## Files to Modify` list is a strong default, not an
  absolute ceiling, when the missing piece is a mechanical, zero-
  judgement port of already-approved design** (e.g. copying CSS rules
  verbatim from a signed-off prototype the task's own Constraints
  already assumed existed) — log it as a scope-internal judgement call
  for human spot-check rather than either improvising silently or
  blocking the whole build on a trivial, zero-ambiguity gap. Found
  live, `REQ-SB-21-US-01-T07`.
- **Composing every backend task around the REAL current file, every
  time, without exception, catches stacked/multiple drifts, not just
  one** — one task hit two independent drifts stacked on the same file
  (async chat/memory work plus a sibling sprint's own keywords
  support). Reading the real file first, every time, caught both before
  either became a silent regression. Reconfirmed, `SPRINT-021`.

### Antipatterns (avoid this)

- **Trusting a stray already-running dev-server process on the
  project's usual port without first confirming what code it is
  actually serving** — it happened to have picked up the same edits via
  its own `--reload` watcher this time, but that is luck, not a
  property that can be assumed next time. Prefer starting a fresh,
  explicitly-controlled instance on a different port when a port
  conflict's root cause cannot be quickly confirmed. Found live,
  `SPRINT-021` (an unkillable stale listener on port 8001).
- **Labeling a verification step's output based on the *intended*
  precondition without an explicit, in-script assertion/set of that
  precondition immediately beforehand** — a disturbed prior state (from
  a killed-mid-flight earlier attempt) can silently invalidate the
  label. Found live, `REQ-SB-21-US-01`'s `AC-07` check.

### Sizing calibration

- **Estimated:** ~9 tasks, L — **Actual:** 9 tasks, L — matched exactly.
  No task was split, dropped, or merged; one task's scope grew slightly
  (absorbing a second, un-anticipated file drift on top of an
  already-known one) but stayed within the same task rather than
  needing a re-estimate.

## 2026-08-12 — SPRINT-023

### Patterns (do more of this)

- **When a locked AC names a specific downstream read function (e.g.
  "discoverable via `list_known_customers()`"), read that function's own
  real implementation FIRST, before trusting a task's own illustrative
  code sample to satisfy it** — `list_known_customers()` scans a
  `customer:` frontmatter field, never the `tags` list; a plausible-
  looking tags-only write would have silently failed this AC without
  re-checking the AC's own exact read path after the first write. Found
  live, `REQ-SB-35-US-01-T02`.
- **When prompting a model for a conditional field ("X, only if the
  content is about a KNOWN Y"), make the "known-or-new" scope explicit
  and test with content about a definitely-new entity, not just an
  already-known one** — a prompt instruction that reads correctly for
  the already-known case can silently mean "existing entities only" to
  the model for the exact case (a brand-new customer/partner) a
  taxonomy-extensibility feature most needs to get right. Found live,
  `REQ-SB-35-US-01-T02`.
- **Prefer direct Python-shell verification over spinning up the full
  HTTP server whenever a task's own Tests block already specifies it
  that way** — generalizes "backend-layer-first live verification" to
  "skip the HTTP layer entirely when it isn't load-bearing for the
  locked ACs," useful when an unrelated app-startup side effect blocks
  the whole server. Found live, `SPRINT-023`.

### Antipatterns (avoid this)

- **Assuming a model-returned field will be populated symmetrically for
  both an "already known" and a "genuinely new" case just because the
  prompt technically allows both** — verify both cases live,
  independently, before treating either as passing. Found live,
  `REQ-SB-35-US-01-T02`.

### Sizing calibration

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S — matched closely.
  The task correctly identified up front as heaviest (a real grounded
  LLM placement decision, 6 of 8 locked ACs) took the majority of build
  time, including two real prompt-iteration cycles.

## 2026-08-12 — SPRINT-022

### Patterns (do more of this)

- **Investigate, don't assume, when an operator correction's own
  reasoning depends on a checkable technical fact** — apply the same
  discipline to a correction's own premise, not just to the feature's
  own output. Confirmed live (Compass/GPT-5 has no real web-search
  capability, verified via the sibling `agentic-map` project's own
  precedent of a separate Perplexity Sonar provider for exactly this
  need) before implementing the operator's Provider-resolution
  correction, turning a potentially-fabrication-risking change into a
  confidently-honest one. Found live, `SPRINT-022`.
- **A sibling project's own already-solved precedent for the identical
  problem is strong, citable evidence** — more convincing and
  load-bearing than reasoning from this codebase's own request shape
  alone. Found live, `SPRINT-022`.
- **When a live network peer is provably stale (confirmed by diffing
  its own response against the newly-registered entity), don't run the
  "real" check against it and report a misleading result — name the
  staleness, and use the strongest available substitute (in-process
  monkeypatch of the real function) instead.** Reconfirmed,
  `REQ-SB-36-US-01-T06`.
- **Split a two-part locked AC's verification honestly** (a
  routing/honesty-funnel half vs. a "produces a real positive result"
  half that's blocked on a genuinely external, unprovisioned
  credential) rather than claiming a full pass or blocking the whole
  task — report exactly what was verified and name the specific
  external blocker, not a vague "partially done." Found live,
  `REQ-SB-36-US-01-T04`/`T05`.

### Antipatterns (avoid this)

- **Assuming a stray dev-server process found via
  `Get-NetTCPConnection` is killable via ordinary means just because a
  prior sprint's identical-looking symptom was** — when multiple
  independent enumeration tools all agree a reported PID doesn't exist,
  don't keep trying the same approach; either pivot to an alternate
  port, or (as later resolved directly, 2026-08-12) find the REAL child
  process via `Get-CimInstance Win32_Process`'s `ParentProcessId` chain
  — a `--multiprocessing-fork` reload worker can still be alive and
  killable even when netstat attributes the listening socket to a
  parent PID that has already vanished from the process table. Found
  live, `SPRINT-022`; resolved same-day without a reboot.
- **A required-Settings-field addition silently breaks the whole app's
  dev-server reload the moment the real `.env` doesn't have it yet** —
  an already-anticipated ADR Consequence, but a real, observed
  operational cost (a managed dev-server process went dark, serving
  stale code, until a placeholder value was added), not just a
  theoretical one. Worth naming explicitly when adding any new required
  config field mid-session. Found live, `REQ-SB-36-US-01-T01`.

### Sizing calibration

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M, but with real,
  unplanned mid-build rework (two tasks built twice, once per the
  original design and once per a mid-build operator correction) plus
  two genuine environmental blockers that consumed real investigation
  time the estimate couldn't anticipate. Task count held; effort within
  the two rebuilt tasks roughly doubled.

## 2026-08-13 — SPRINT-024

### Patterns (do more of this)

- **When a locked task Constraint says "no step may fabricate a result"
  and a composed real dependency can raise rather than return, add the
  `try/except` — this is satisfying the AC's own honest intent, not
  scope creep.** Extends `graph.py::_call_model`'s own precedent to a
  second, non-graph call path. Found live, `REQ-SB-36-US-02-T02`.
- **When a task's own sample proposes reusing an existing shared
  dispatch function for a new, differently-shaped handler, verify the
  existing function's own real handler-calling convention before wiring
  the new entry in** — a shape mismatch is silent at import time and
  only surfaces at first real invocation. Add a NEW sibling function
  alongside the existing one, rather than generalizing/branching inside
  it, whenever the existing function is also relied on synchronously by
  a caller outside the current task's own file scope. Found live,
  `REQ-SB-36-US-02-T03`.
- **A generic, non-action-specific flag on a shared response envelope**
  (e.g. `"history_recorded"`) resolves a "the generic post-processing
  double-records a self-recording handler's own outcome" tension without
  special-casing by action/agent id — reusable by any future handler
  with the same self-recording shape. Found live, `REQ-SB-36-US-02-T03`.
- **When an established test-content technique from an earlier sprint
  stops working because the vault's own real taxonomy has since
  materialized the exact catch-all kind that content used to force a
  new area under, don't fight the model — reframe the content to
  genuinely warrant a dedicated area.** The methodology-grounded model
  was behaving correctly against the real, current vault state; the
  test technique needed to catch up to reality, not the reverse. Found
  live, `REQ-SB-36-US-02-T02`.
- **Splitting verification honestly when one specific step is blocked
  on an unprovisioned external credential** (real for everything
  reachable; a clearly-disclosed, reverted substitution for the one
  externally-gated piece) — reconfirmed a second time
  (`SPRINT-022`→`SPRINT-024`) as the right call over either claiming a
  full pass or blocking the whole task on an environment gap outside
  the sprint's own control.

### Antipatterns (avoid this)

- No new antipattern this sprint beyond ones already carried forward —
  worth noting explicitly: a 5-sprint dependency chain
  (`SPRINT-020`→`024`) completed with every composed real function from
  prior sprints holding up exactly as documented, zero surprises in
  their own contracts — the friction was entirely at this sprint's own
  new dispatch-layer seams, not in reused prior work.

### Sizing calibration

- **Estimated:** ~3 tasks, S (buildable) — **Actual:** 3 tasks, S,
  matched exactly. The orchestration task was correctly identified up
  front as the real cost center — not in code volume, but in
  live-verification complexity (two independent honest-failure paths, a
  real content-engineering iteration, a load-bearing exception-handling
  finding only surfaced by actually invoking the real composed chain).

## 2026-08-13 — SPRINT-025

### Patterns (do more of this)

- **When a "start the real server" verification step is blocked by a
  known, already-logged app-startup issue, don't default to the weakest
  possible substitute — find the closest-to-real substitute that still
  exercises what the AC actually needs proven** (`TestClient` without
  lifespan for a real HTTP-routing AC; the literal real trigger function
  via `asyncio.run` for a real "does the wiring fire automatically" AC)
  — both are disclosed verification-method deviations, not silent AC
  weakenings. Found live, `SPRINT-025` (`BUG-008`).
- **Before assuming a known, logged issue explains a new hang, isolate
  and test its actual named cause in isolation first** — a bounded,
  standalone check proved the named cause (Outlook COM) was fine,
  redirecting investigation toward the real, more likely cause (multiple
  real per-email LLM classification calls) rather than mis-attributing a
  slow-but-working pipeline to the wrong failure mode. Found live,
  `SPRINT-025`.
- **A locked AC's own exact-match verification step is itself a real
  correctness assertion, not just illustrative prose** — when it
  genuinely fails against live data, root-cause it fully before deciding
  whether it's a build defect or an environmental/out-of-scope finding,
  then escalate the latter formally rather than loosening the check to
  make it pass. Found live, `REQ-SB-01-US-01-T02` (`ESC-027`).
- **Killing a hung background process by its own specific,
  timestamp-verified PID, leaving unrelated concurrent processes alone**
  — this project's own repo can have genuine concurrent work landing in
  real time; a blanket kill risks another session's own in-flight work.
  Reconfirmed, `SPRINT-025`.

### Sizing calibration

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  The core index module was correctly identified as the cost center, but
  the actual time went to a real filename-collision investigation
  (`ESC-027`), not the index logic itself, which built clean on the
  first pass.

## 2026-08-13 — SPRINT-029

### Patterns (do more of this)

- **`httpx.ASGITransport(app=app, client=(fake_ip, fake_port))`, with a
  plausible (not arbitrary) Host in `base_url`, is the correct default
  technique for verifying an ASGI-middleware-level auth/network-origin
  check that cannot be exercised via a real non-loopback network path in
  a dev environment** — genuinely drives the real, unmodified
  application object, not a mock. Found live, `REQ-SB-04-US-01-T01`.
- **When a task's own Tests block deliberately verifies plumbing via a
  seeded/bypassed front door for an honestly-documented reason (a
  fail-closed seam not yet real), add one extra, clearly-labeled real
  end-to-end check against the actual front door** to independently
  confirm it behaves exactly as designed for whichever behaviour it CAN
  exhibit today — cheap additional confidence beyond what the task's own
  named steps strictly require. Found live, `REQ-SB-04-US-01-T02`.
- **The specific-PID-kill-and-restart protocol, reconfirmed a fourth
  time** (`SPRINT-019`/`021`/`022`/`029`) — a stray `--reload` uvicorn
  process plus its own separately-alive multiprocessing-fork child was
  found holding the dev port; killing both and starting a single,
  explicitly-controlled instance kept verification unambiguous.

### Antipatterns (avoid this)

- **Assuming an arbitrary placeholder hostname is inert for any
  ASGI-transport-based test against a real third-party ASGI
  sub-application** — some sub-applications (here, FastMCP's own
  transport) validate the Host header themselves, independent of
  whatever is actually being tested; use a plausible real host matching
  what a genuine client would send. Found live, `REQ-SB-04-US-01-T01`
  (cost one debug cycle — a `421 Misdirected Request` unrelated to the
  auth middleware under test).
- **A shared dev vault can carry real concurrent-session drift in its
  live content, not just shared source files** — an app-start capture
  pass crashed once on a transient race (a concurrent session's own
  throwaway test file, deleted between glob and read). Not a defect in
  the sprint's own code; resolved by a plain retry once vault state
  stabilized. Found live, `SPRINT-029`.

### Sizing calibration

- **Estimated:** ~2 tasks, S (buildable) — **Actual:** 2 tasks, S —
  matched exactly. The auth middleware was small in code volume but
  needed a genuinely non-trivial verification technique; the tool+
  plumbing task was correctly sized as the heavier of the two.

## 2026-08-13 — SPRINT-027

### Patterns (do more of this)

- **When a task's own named induction technique for a real external
  system's "unreachable" state doesn't actually stick (auto-recovery
  behaviour of the real dependency itself), fall back to this project's
  own established in-process-monkeypatch technique rather than accepting
  a weaker, backend-only proof** — for a screen-level AC, monkeypatch the
  dependency before importing the real app, temporarily swap it in on
  the same port the frontend is already wired to, screenshot, then
  revert, keeping the verification genuinely end-to-end. Found live,
  `REQ-SB-11-US-01-T04` (`AC-05` — Windows COM silently auto-relaunches
  Outlook.exe on the next connection attempt, even after a forced kill).
- **The OS-installed Edge browser's own headless screenshot mode
  (`msedge.exe --headless=new --screenshot=... URL`) is a real,
  legitimate, zero-new-dependency substitute when no visual-harness/CDP
  tool is available** — a real browser engine against the real dev
  server, not a mock. A large `--window-size` height plus a
  `System.Drawing`-based crop (PowerShell) reaches content below the
  fold without a real scroll interaction. Found live,
  `REQ-SB-11-US-01-T04`.
- **A real background/scheduled real-Provider capture tick's own latency
  is genuinely variable run-to-run** (~90s on one app-start tick, ~6-7
  minutes on a later restart of the same unmodified code) — reconfirms
  `SPRINT-021`'s own "assume multi-minute latency, don't assume a hang"
  entry; checking the waiting process's own accumulating CPU time (not
  just wall-clock elapsed) cheaply distinguishes "still genuinely
  working" from a true hang. Found live, `SPRINT-027`.
- **Composing a fix directly around the REAL current file caught two
  independent, real, concurrent-session drifts in one pass** (a sibling
  sprint's own scheduler-tick addition; another concurrent session's own
  router/page additions to shared files) — this project's own
  established pattern held up a further time. Reconfirmed, `SPRINT-027`.

### Antipatterns (avoid this)

- **Assuming `npx`/`tsc` are resolvable on PATH in every session/shell**
  — neither shell in this session could resolve `npx`, even though the
  project's own running Vite dev server proved Node/npm were installed
  somewhere. A live Vite-transform fetch of the changed module is a
  reasonable fallback confirming no syntax error, but should be named
  explicitly as narrower than `tsc -b`, not conflated with one. Found
  live, `REQ-SB-11-US-01-T04`.

### Sizing calibration

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  The frontend task was correctly the heaviest by verification effort,
  not code volume — real screen-level proof for all 7 ACs needed real
  tool-improvisation (the headless-Edge screenshot substitute), not
  extra code-writing.

## 2026-08-13 — SPRINT-026

### Patterns (do more of this)

- **React-controlled-input CDP verification** — always set values via the
  native `HTMLInputElement.prototype.value` setter
  (`Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,
  'value').set.call(input, value)`) before dispatching a synthetic
  `'input'` event, not a plain `.value =` assignment — the latter
  silently no-ops against React's own internal value tracker. Found
  live, `REQ-SB-02-US-01-T04`.
- **SPA-internal remount (nav-away/nav-back), not `Page.reload()`, to
  re-trigger a component's mount-time effect while keeping an in-page
  `window.fetch`/monkeypatch stub alive** — a hard reload wipes any
  same-context JS override; a client-side route change does not. Found
  live, `REQ-SB-02-US-01-T04` (`AC-07`).
- **Scope a CDP-launched headless Chrome's own cleanup kill to its
  specific PID tree** (`taskkill /PID <pid> /T /F`), never `/IM
  chrome.exe` — `SPRINT-009`'s own antipattern, reconfirmed worth
  actively avoiding.
- **Layer-by-layer live verification** (function calls → real HTTP →
  real browser) catches every issue at the cheapest possible layer.
  Reconfirmed, `SPRINT-026`.

### Antipatterns (avoid this)

- **Trusting a decomposer-authored "matches nothing" example query
  verbatim against a large, real, organically-grown text corpus**
  without first checking whether its sub-tokens happen to be real,
  common words — verify (or substitute a genuinely opaque single token)
  before relying on it as an honest-empty-result test case. Found live,
  `REQ-SB-02-US-01-T02` (`AC-05`).
- **Silently trusting a first no-op CDP interaction** instead of adding
  `Console`/`Runtime.exceptionThrown` listeners and a minimal debug
  harness the moment a result looks suspicious — both real issues this
  sprint would have been faster to isolate with observability wired in
  from the start rather than added reactively. Found live,
  `REQ-SB-02-US-01-T04`.

### Sizing calibration

- **Estimated:** ~4 tasks, M — **Actual:** 4 tasks, M — matched. The
  frontend task was genuinely the heaviest as predicted, but not
  disproportionately so; the straight dependency chain meant zero
  rework/reordering.

## 2026-08-13 — SPRINT-028

### Patterns (do more of this)

- **When an ADR discloses a claim it could not empirically verify and
  assigns the coder a live-verification step, treat that step as
  load-bearing, not a formality** — run it for real, record the result
  explicitly (confirmed or superseding-ADR-worthy), and close the loop
  in the story's own gate reasoning. Found live,
  `REQ-SB-09-US-01-T01`/`T03` (the `EntryID`-stability claim, confirmed
  correct).
- **Bound a live-data verification to a real, filtered subset via
  in-process monkeypatch of the real fetch function, rather than
  re-running a full real capture for every single check** — real data,
  real dependencies, bounded cost. Generalizes `SPRINT-022`/`SPRINT-024`'s
  own failure-induction pattern to scope-bounding as well. Reconfirmed,
  `SPRINT-028`.
- **Independently confirm a new mechanism is correct via a controlled
  case BEFORE attributing a real-data failure to that mechanism** — a
  short-subject control pair proved the new disambiguation logic was
  sound, which is what made it possible to confidently root-cause a
  long-subject collision to pre-existing, out-of-scope infrastructure
  instead of second-guessing the new code. Found live,
  `REQ-SB-09-US-01-T03` (`ESC-028`/`BUG-011`).

### Antipatterns (avoid this)

- **Assuming a stray dev-server process on the project's own usual
  ports is safe to build against without confirming what it's serving**
  — reconfirmed a further time this session. Kill and restart an
  explicitly-controlled instance.
- **Assuming `npx`/`node`/`npm` are resolvable on `PATH` in every
  session/shell** — a second confirmed instance (first found
  `SPRINT-027`); worth fixing at the environment/session level. When it
  recurs, locate the real install via the registry (`HKLM:\SOFTWARE\
  Node.js`) rather than assuming Node isn't installed at all.

### Sizing calibration

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly.
  The two heaviest tasks were correctly identified up front by
  verification effort (real, multi-minute Compass-backed capture runs),
  not code volume.

## 2026-08-10 — Book reference, not a sprint retro

No sprint has run yet — this entry deviates from the file's own protocol
(harvested from retros, human-propagated) at the operator's explicit
request, since *Beyond the Second Brain* (Mo Elkholy) produced real
heuristics worth having on hand before the first retro exists. Source:
`Documentation/References/beyond-the-second-brain-methodology.md`. Treat
this entry as provisional against real sprint experience, not as
equivalent-weight to a harvested retro.

### Patterns (do more of this)

- **Tags for multidimensional attributes, folders only for single-home
  ones** — confirmed live via `ADR-004`: `Customer` (multi-valued, can
  change) became a tag; `Kind` (stable, single-valued) stayed a folder.
  Apply the same test to any future categorization axis before adding a
  folder level for it.
- **Self-explanatory notes ("context is the currency")** — a note destined
  to feed an AI synthesis session should be understandable without the
  conversation that produced it. Worth applying explicitly once synthesis
  features exist, not just capture ones.
- **Forward-only linking** — Obsidian computes backlinks automatically from
  `[[wikilinks]]`; the conversation-thread linking only writes a link on
  the *newer* note, never edits older ones. Prefer this shape (write once,
  let the graph compute the reverse) over any pattern that requires
  updating multiple existing notes when a new one arrives.
- **Design for the extensibility point, not the enum** — `kind`/`customer`
  are Compass-proposed and vault-derived, never a hardcoded list. When a
  future classification axis appears, prefer "read what's already there,
  let the model propose new values" over enumerating options in code.

### Antipatterns (avoid this)

- **Raw capture treated as a finished note** — every note so far is a full
  raw email body, not a distilled one-idea note (the book's "atomic notes"
  principle). Not yet fixed; flagged so it isn't mistaken for done.
- **Entity-first structure with no output orientation** — the vault
  organizes around *who* (Customer) with nothing yet organized around
  *what gets produced* (a decision, an account plan, a proposal). The book
  calls a topic/entity taxonomy that maps to no output "the design trap."
- **Assuming a natural key is unique** — date+subject collided in
  production (two same-day duplicate notifications overwrote each other).
  Always include a genuinely unique identifier (e.g. source system ID) in
  any generated filename/key, even when a collision seems unlikely.

## 2026-08-14 — SPRINT-030

### Patterns (do more of this)

- **Trace a task's own illustrative sample code's real call graph before
  running it, not just after a crash** — caught a genuine infinite-
  recursion bug (`_load_state()` calling `grant_skill_access()`, which
  itself calls `_load_state()`) before it ever executed. Also caught a
  `KeyError`-on-success bug in a different task's sample the same way.
  Both were shipped-looking illustrative code, not obviously wrong on a
  read-through alone.
- **`TestClient` (fast, no full app-start) plus a real `curl` against a
  fully-started server (slow, real side effects) are not either/or** —
  run both when a real app-start side effect makes the full server slow
  to bring up; the fast layer gives immediate real evidence, the slow
  layer is free bonus rigor once it finishes in the background.
- **Back up real production state, run a deliberate clean-slate test,
  then restore it** — reused for `.second-brain/agent_skills.json`
  around a migration-seed verification; correctly distinguished
  real pre-existing production grants from the task's own new output
  before restoring.

### Antipatterns (avoid this)

- **Assuming a git worktree's checked-out state matches the main
  checkout's real current working tree** — true only for files the main
  checkout's own `git status` reports clean. Every `M`/`??` file (a large
  set on an actively-developed repo) needs an explicit sync before a
  worktree's copy can be trusted for reading OR appending. Also:
  `tools/node/` (like `.env`/`.venv`) is gitignored and therefore also
  absent from a fresh worktree — a worktree-run coder's own "X is not
  installed on this host" claim should be read as "X was not reachable
  from this isolated worktree," not trusted as a host-wide fact (the main
  checkout had a working portable Node the whole time). See `MEMORY.md`
  for the full correction.
- **Triggering a real Outlook/Compass app-start capture pass just for an
  HTTP-routing confirmation, when a lighter technique (`TestClient`)
  already gives equivalent real evidence** — valuable as bonus
  confirmation, but shouldn't be the first or only attempted route when
  time is scarce.

### Sizing calibration

- **Estimated:** ~9 tasks, L — **Actual:** 9 tasks, L — matched exactly.
  The heaviest tasks were heaviest by real verification cost, not code
  volume — each surfaced a genuine correctness bug in its own sample
  code that only a real live run found.

## 2026-08-14 — SPRINT-031

### Patterns (do more of this)

- **Independently test an operator-named "single highest-risk check" as
  its own small, fast, isolated probe FIRST, using a different agent/
  input than any slower, already-planned end-to-end test** — de-risked
  the sprint's single most safety-critical property (a real migrated
  mutating Skill under Supervised mode defers rather than executes) in
  0.008s, without making its confirmation depend on a much slower
  real-world call succeeding.
- **Live CPU-accumulation + active-TCP-connection checks as a genuine
  "still working, not hung" control** — used across a multi-hour real
  background run (a full, unbounded, on-demand real Meetings-backlog
  capture) to distinguish real bounded progress from a true hang without
  ever needing to kill and restart.

### Antipatterns (avoid this)

- **Assuming an "S"-sized task's real-world verification cost scales
  with its code volume** — this sprint's code diff was genuinely small,
  but one single mandated live check (an unbounded, on-demand real-
  pipeline invocation against a large real backlog) dominated the
  sprint's actual wall-clock cost by orders of magnitude. Flag this
  explicitly whenever a task's Tests block names an unbounded, on-demand
  real-pipeline invocation as its verification method.
- **Not proactively checking for a stray, already-running dev-server
  process sharing the same real vault/working-mode state before starting
  a live Supervised-mode test** — a real, unattended background-scheduler
  tick from a process running since before the session started created
  its own real pending-approval record mid-test. A quick
  `Get-NetTCPConnection -LocalPort 8000,8001` at the START of live
  verification would have surfaced this proactively instead of mid-test.

### Sizing calibration

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S in code volume, but
  real verification cost was well outside the "S" envelope — one manual
  test step against a large real backlog took several real-world hours.
  No prior Learnings entry's documented latency range (90s–7min, for a
  scheduled tick) anticipated a full on-demand backlog run being this
  much larger. Consider flagging "unbounded real-pipeline invocation" as
  its own wall-clock-risk sizing dimension, separate from code volume.

## 2026-08-14 — SPRINT-032

### Patterns (do more of this)

- **Verify a retrieval mechanism honestly against the vault's OWN real
  current content, never fabricate a positive result for a schema with
  no real data yet** — confirmed `Work/Pipeline`/`Agreements`/
  `Consumption` don't exist in the real vault at all, used the closest
  real substitute (the `customer/<slug>` tag) for the positive case,
  and independently confirmed the literal empty-schema case honestly
  returns `"empty"`. Disclosed directly in the task/story, not glossed
  over.
- **A minimal Python `websockets` CDP driver (no `node`/`npx`/Playwright
  needed) combined with the React-controlled-input Fiber-props direct-
  invoke technique** — drove a real click → tab-switch → type-and-commit
  → close/reopen-persistence round trip against the real running
  frontend with zero extra dependencies.

### Antipatterns (avoid this)

- **Fire-and-forget `Start-Process` for a headless-browser launch meant
  to be debugged** — silently exited within ~1s with no diagnostic;
  switch to a foregrounded, output-redirected invocation first when a
  headless launch needs debugging.
- **Sharing one CDP WebSocket connection for both synchronous
  request/response RPC and event-stream listening** — hit a
  `ConcurrencyError` from two coroutines both calling `recv()`. Open a
  second WebSocket connection to the same target for event listening.

### Sizing calibration

- **Estimated:** ~5 tasks, S — **Actual:** 5 tasks, S — matched exactly.
  The two heaviest tasks were heaviest by which live-verification
  technique they demanded (CDP round trip; honest real-vs-schema
  finding), not code volume — both built in under 40 lines.

## 2026-08-14 — SPRINT-033

### Patterns (do more of this)

- **When a task's own informal verification-step prose names a URL that
  isn't quoted from a locked AC, verify the real route from the router's
  own source file before trusting it** — one task's prose named
  `/agents-map`; the real mounted route was `/` (root). Cheap to catch
  with a `grep`, cheaper than debugging a blank-page screenshot after.
- **A CDP WebSocket driver (own `Runtime.evaluate`/`Page.navigate`/
  exception listener against a dedicated `--remote-debugging-port` +
  `--user-data-dir` headless profile) proves exact interaction
  sequencing/network-call-count**, not just "does it look right" — a
  `window.fetch` spy confirmed zero calls on an empty-submission path
  and exactly the wizard's own two-call sequence, in order, on real
  submission.
- **Run one extra, sprint-level (not task-level) end-to-end pass before
  closing a sprint that introduces a genuinely new mechanism class** —
  here, the first-ever runtime-created agent. A fresh agent's real
  Chat/History/Settings tabs and the honest-uncertainty guardrail were
  all directly exercised, plus a before/after reconfirmation that the 7
  static agents stayed byte-identical — cheap, and turned "the individual
  ACs all passed" into directly-observed "the whole feature genuinely
  works."

### Antipatterns (avoid this)

- **Assuming a bash-emulated PID from a command this same task launched
  (`nohup ... &`, `echo $!`) is a real, killable Windows PID** —
  reconfirmed again; always resolve the real PID via
  `Get-NetTCPConnection`/`Get-CimInstance Win32_Process` before
  `Stop-Process`/`taskkill`.

### Sizing calibration

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — matched exactly.
  `ADR-030`'s own predicted mechanism ("zero code changes needed in any
  of the five self-healing per-agent registries") held up exactly as
  designed on first try, independently reconfirmed live, not just
  trusted.

## 2026-08-14 — SPRINT-034

### Patterns (do more of this)

- **Cross-check a freshly-created agent's behavior against an existing,
  already-shipped agent's own identical call, live, in the same
  session** — turned "the gate probably behaves the same for a new
  agent" into a directly-observed, byte-identical confirmation. Applies
  this project's own cross-check pattern one layer up, at the
  agent-creation layer.
- **After ANY edit to a file a running `--reload` server is watching,
  re-confirm the new behavior with one cheap real request before running
  a task's full Tests sequence against it** — a rapid two-file edit
  sequence (~1 minute apart) caused `WatchFiles` to silently miss the
  second file's change; caught early because a smoke check ran first.

### Antipatterns (avoid this)

- **`taskkill /IM msedge.exe /T` for CDP-launched-browser cleanup** —
  this project's own Learnings already name the specific-PID form as
  required (`SPRINT-026`); the `/IM` form was used once out of habit
  before self-correcting. No observed harm this time, but the risk
  (killing an unrelated session's own browser instance) is real —
  follow the documented technique from the first launch, not after a
  reminder.
- **Checking `.second-brain/` state-file cleanliness at
  `src/backend/.second-brain` instead of the real, `.env`-configured
  `VAULT_PATH`** — cost an avoidable investigation cycle. This project's
  vault is *always* external to `src/`; any "delete leftover state files
  first" instruction means the real `VAULT_PATH`, never a guessed
  in-repo path.

### Sizing calibration

- **Estimated:** ~5 tasks, S — **Actual:** 5 tasks, S — matched exactly,
  zero mid-build reconciliation surprises beyond ordinary file-drift
  checks.

## 2026-08-14 — SPRINT-035

### Patterns (do more of this)

- **When a locked AC needs a real positive outcome from a multi-hop
  composed chain the real vault's current configuration can't reach
  as-is, temporarily reconfigure real state through the app's own
  already-`Done` APIs (a skill grant, a Provider swap, a Section
  reassignment), verify, then revert and independently reconfirm the
  revert** — stronger evidence than a mock, bounded and reversible since
  it goes through real, already-trusted endpoints. Extends the
  "closest-to-real substitute" precedent to a multi-step Hub-routing
  scenario.
- **Read the turn's real `HumanMessage` instead of trusting a tool-call
  argument the model itself generated** — directly confirmed live: the
  recorded value was the full real question, not the model's short
  paraphrase.

### Antipatterns (avoid this)

- **`uvicorn --reload`'s `WatchFiles`-triggered restart can silently
  keep serving the OLD worker's routes for an extended period when a
  long-running background asyncio task is in flight at the moment of
  reload** — a newly-added route returned a bare `404` against the still-
  old worker for several interleaved requests. Fix: kill both the
  reloader parent and its child worker PID, start one fresh
  non-`--reload` instance for the rest of the session.
- **Assuming an established "obscure/nonsensical subject" no-results
  test technique still reliably produces an honest `"no_results"` once a
  real web-search Provider is genuinely reachable** — a real privacy-
  refusal reply from the model was itself treated by the composed chain
  as a "found" result and filed. Not a defect in the new sprint's own
  code — a real, disclosed finding about the already-shipped chain's own
  behavior. "The model declines to answer" and "genuinely no relevant
  content exists" are two different real conditions one obscure prompt
  can hit.
- **Edge's own CDP `/json/new` endpoint requires `PUT`, not `GET`, on
  newer installed versions** — a real, version-specific break from
  older example code; check directly (`curl -X PUT`) rather than
  assuming GET still works.

### Sizing calibration

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L — matched exactly.
  Extending an already-proven tool-interception pattern a second time
  took little code; genuinely proving it live, plus proving the shared
  conversation graph's ordinary-chat behavior was unaffected on 2
  separate agents, was the real cost.

## 2026-08-14 — SPRINT-036

### Patterns (do more of this)

- **A minimal Node+native-`fetch`+native-`WebSocket` CDP client (no
  `puppeteer`/`playwright`/`ws` package) is a fully adequate substitute
  for a proper e2e harness** — real browser, real DOM, real network
  calls, real React state, verified two genuine state mutations
  end-to-end including server-side persistence across a panel
  close/reopen.
- **Locate a project's own bundled Node install via the actual running
  dev-server process's own executable path**
  (`Get-Process -Id <pid> | .Path`), not just a registry lookup — faster
  and more direct than the previously-documented technique.

### Antipatterns (avoid this)

- **Reading a `<select>`/`<input>`'s value in the SAME synchronous CDP
  `Runtime.evaluate` call as the click/dispatch that changes it** — races
  ahead of React's state-flush-then-rerender cycle, producing a false-
  negative stale read. Extends the already-documented `onBlur`-commit
  precedent: add a short (~500-1000ms) real wait between ANY
  CDP-dispatched state change (including plain `onClick` tab switches)
  and reading the resulting DOM back — not just synthetic-event edge
  cases.

### Sizing calibration

- **Estimated:** ~2 tasks, S — **Actual:** 2 tasks, S — matched exactly.
  The frontend task's real diff was small, but proving all 7 locked ACs
  live across 3 different agent-type spot checks needed a genuinely
  non-trivial CDP session — verification cost, not code volume, drove
  the real effort.

## 2026-08-14 — SPRINT-037

### Patterns (do more of this)

- **Design a data-model split (e.g. "overview shows less than
  everything") to structurally guarantee an AC by construction, not an
  added runtime check** — grouping by `(sectionId, agentType)` made
  "a cluster marker never mixes Types" true by construction; zero extra
  defensive code needed, held up exactly as predicted.
- **When a task's Objective can only be achieved by touching a file one
  layer up the component tree that no task declared, and the fix is a
  mechanical, same-pattern extension of that file's own already-
  established shape (zero new business logic, no new interface for any
  other consumer) — implement it, log it explicitly as a scope-internal
  judgement call, flag the task's gate for human spot-check.** Neither
  silently expand scope unflagged, nor block an otherwise-complete,
  locked story on a plumbing-only gap.

### Antipatterns (avoid this)

- **A decomposer's per-task `## Files to Modify` list, even when each
  task is individually correct and passes its own tests in isolation,
  can still miss a cross-file integration consequence of an earlier,
  already-frozen task's own locked design choice** — specifically,
  wherever an earlier task *reduces* a shared data shape (here,
  `mapAgents`) ahead of a later task that *reuses* the old, larger
  shape. Worth an explicit "does this reduction alter what flows through
  to an unlisted, up-the-tree caller" question during future
  decomposition passes for any "overview shows less, but a drill-down
  still needs everything" shape.
- **Verify a locked AC's own "must not narrow existing behavior"
  Constraint live, before assuming the straightforward wiring is
  sufficient** — reading the code alone made this look like a one-file
  task; only the live full-drilldown check surfaced the gap above.

### Sizing calibration

- **Estimated:** ~4 tasks, S — **Actual:** 4 tasks, S — task count
  matched; the heaviest task's real cost was an only-discoverable-at-
  integration-time gap (above) plus live-clustering verification against
  real, disposable test agents.

## 2026-08-14 — SPRINT-038

### Patterns (do more of this)

- **`httpx.ASGITransport(app=app)` against the real, unmodified `app`
  object, combined with a scoped in-process monkeypatch, induces a real
  failure for one specific HTTP call with no permanent code edit** —
  genuinely drives the real app through a real HTTP request/response
  cycle, not a mock. Reusable for any future business-logic
  failure-induction need.
- **`DOM.setFileInputFiles` is the correct CDP primitive for real
  file-input interaction** — a native-setter/`dispatchEvent` technique
  cannot set `.files` on a file input at all (browsers block it).
- **Directly `await import(...)`-ing the real, served frontend module
  from the browser's own JS console tests a code path the UI's own
  client-side pre-check structurally prevents from ever being reached
  through ordinary interaction** — exercises the real, unmodified module
  function against the real server, distinct from and complementary to
  the UI-level rendering confirmation for the same server-side branch.

### Antipatterns (avoid this)

- **Assuming a project's default CORS allow-list "just works" against a
  freshly-started dev-server instance on a non-default port** — the
  backend's `CORSMiddleware` only allows `5173`/`5174`; a frontend
  started on `5180` silently failed with no visible error beyond an
  empty "No agents connected yet." state. Check the allow-list BEFORE
  picking a verification port, not after hitting the confusing
  empty-state symptom.
- **Hand-building a minimal real PDF byte-by-byte (raw object/xref/
  trailer structure) when no PDF-authoring library is installed** —
  worked, but is fragile and easy to get wrong; worth naming explicitly
  as the fallback technique rather than reinventing it next time.
- **Windows console codepage (`cp1252`) can silently mangle non-ASCII
  script output** (em-dashes, emoji) — looked like data corruption until
  a UTF-8 file round-trip confirmed the underlying data was always
  correct. Wrap `sys.stdout` in a UTF-8 `TextIOWrapper` (or write to a
  file) by default for any verification script expected to print
  non-ASCII content.

### Sizing calibration

- **Estimated:** ~5 tasks, S — **Actual:** 5 tasks, S — matched exactly.
  Every locked AC across all 10 story-level scenarios was verified live
  with a real positive result — no environment-blocked/deferred half,
  unlike several recent prior sprints.

## 2026-08-16 — SPRINT-048

### Patterns (do more of this)

- **Generic-primitive-first, kind-specific-wrapper-second, for any story
  introducing 2+ structurally-identical note/entity kinds in sequence** —
  build the shared mechanism once against the FIRST concrete kind
  (`replace_body_section`; the `okf_directory_*` directory family), then
  apply it to every subsequent kind as thin wrappers only (Project's five
  one-line-bodied functions, reusing Customer's own generic mechanism
  verbatim, zero duplicated 4-file-creation logic). Found live,
  `REQ-SB-54-US-01-T01`/`T04`/`T05`.
- **A one-level discovery glob is a real, structural blind spot the moment
  ANY note kind gains a directory shape — make the fix its own explicit
  task, not an assumed side effect of the kind-adding task.** Naming
  `list_all_note_paths()`'s gap explicitly (rather than letting the
  directory-adding tasks silently absorb it) turned it into a real,
  separately-verified task instead of a latent bug a future search/
  indexing pass would have silently hit. Apply whenever a future story
  adds a note kind whose files don't all live at the same folder depth as
  every existing kind. Found live, `REQ-SB-54-US-01-T06`.
- **When restructuring a function's internals that has multiple real
  external call sites, preserve the external contract exactly and verify
  every call site is unaffected, rather than touching the call sites
  too** — `customer_hub_linking.ensure_customer_hub_note`'s restructure
  kept its exact return shape and all 5 real callers working with zero
  changes to any of them, confirmed live-by-reasoning against each one.
  Found live, `REQ-SB-54-US-01-T04`.

### Antipatterns (avoid this)

- **Nesting a real, specific disclosed risk inside a broader, more-
  easily-resolved `REVIEW-QUEUE.md` entry (e.g. "and also, separately,
  X").** When the broader entry is cleared, the nested disclosure
  disappears with it even though it was never itself resolved — a real
  gap (`migrate_customer_to_partner` silently no-op-ing for any Customer
  created under the new OKF directory shape) was lost this way when the
  broader `ADR-042` review item was cleared, and had to be re-filed as
  its own standalone item. Give any genuinely separate, future-relevant
  risk its OWN `REVIEW-QUEUE.md` line item, even when it surfaces
  mid-discussion of a larger one. Found live, `SPRINT-048`.

### Sizing calibration

- **Estimated:** ~6 tasks, M — **Actual:** 6 tasks, M — matched exactly,
  extending the same precedent already noted for `SPRINT-020`/
  `SPRINT-022`/`SPRINT-028` (all exactly-6-task sprints sized M that
  matched at retro). The heaviest task (the OKF directory family plus a
  live-internals restructure preserving 5 real call sites) was correctly
  predicted at sizing time by its live-verification complexity, not code
  volume; the lightest task (closing the sprint) was a direct, literal
  implementation of its own illustrative code with zero deviation.

## 2026-08-16 — SPRINT-049

### Patterns (do more of this)

- **Sequence a downstream story strictly behind its upstream one via
  `depends_on_sprints`, rather than combining into one oversized sprint,
  when the downstream story's own Tests block requires the REAL, running
  output of the upstream story** — confirmed a further time
  (`SPRINT-011`→`012`, `025`→`026`, now `049`→`050`): `REQ-SB-63-US-01-T02`
  could not have been built or verified against a stub, since its own
  Tests required a real `thread_result` from a real, compiled
  `email_capture_pipeline.py` graph. Building the downstream sprint only
  after the upstream one closes means the downstream task never has to
  improvise a divergent shape against an imagined interface.
- **A single story's own dependency chain, even when it fans out into a
  diamond (two independent roots converging through several branches into
  one assembly task), stays one sprint** — `REQ-SB-55-US-01`'s 8-task
  chain (`T01`/`T02` independent roots → `T03` → `T04`/`T05` → `T06` →
  `T07` assembly → `T08` retirement) built cleanly end-to-end with zero
  reordering once the graph was correctly recorded at `/plan-tasks`.
- **Verify a "structural, not hardcoded" detection requirement against a
  GENUINELY unrelated real test case** (a different, fictitious customer,
  different structural shape) as the actual load-bearing AC check, not
  just a second example of the same known shape — this is what actually
  proves the mechanism generalizes rather than memorizing one customer's
  format. Found live, `REQ-SB-55-US-01-T02`/`T06`.
- **When a task's own Constraints wording and its End-State/illustrative
  text disagree on a narrow mechanical point (e.g. exactly which module an
  import may live in), reconcile by following the End-State text and
  log the reconciliation as a scope-internal judgement call** — do not
  silently pick one without disclosure, and do not treat the disagreement
  itself as a blocking escalation when the two are reconcilable by reading
  both carefully. Found live, `REQ-SB-55-US-01-T07`.

### Antipatterns (avoid this)

- Nothing sprint-blocking this sprint. Worth naming: a genuinely large
  (8-task) single-story sprint is buildable in one continuous session
  without reordering ONLY when the decomposer's own dependency graph was
  read correctly the first time — any task built out of its recorded
  `depends_on` order against a still-forming shared module risks a
  conflicting edit that a strict sequential build order avoids entirely.

### Sizing calibration

- **Estimated:** ~8 tasks, L — **Actual:** 8 tasks, L — matched exactly,
  extending the `SPRINT-010`/`SPRINT-039` 8-task/L precedent and sitting
  just under this project's own largest confirmed-accurate ceiling
  (`SPRINT-021`/`SPRINT-030`, 9 tasks/L). `T07` (pipeline assembly) and
  `T08` (retirement + the mandatory real, live Outlook-backed end-to-end
  run) were, as predicted, the heaviest by live-verification effort, not
  code volume — `T08`'s real run produced a genuine new Thread note and a
  genuine new Pending Approval in the real, configured vault.

## 2026-08-16 — SPRINT-050

### Patterns (do more of this)

- **"Propose in the Expert's own module, finalize in the router's dispatch
  table" (`_create_X_proposal` + `finalize_X`, registered in
  `_APPROVAL_HANDLERS`) is now a 3x-confirmed canonical shape for any new
  Pending-Approval kind** (`ADR-021`'s original Tier-2 proposal,
  `SPRINT-049`'s `route_thread_to_project`/`propose_recurring_pipeline`,
  `SPRINT-050`'s `propose_cross_cutting_update`) — default to this shape
  for any future new approval kind without re-deriving it.
- **When adding an unconditional additional branch alongside an existing
  single-choice conditional edge from the same `StateGraph` source node,
  convert the routing function to return a LIST (`"always this" +
  conditionally "also that"`), mirroring the existing "always this,
  additionally that" shape** — do not invent a second, parallel wiring
  mechanism for the same node. This made a "never gates the existing
  branch" Constraint a structural graph-topology property (two independent
  destinations, each with its own fixed edge to `END`) instead of
  something enforced only by code review.
- **A Job-tier caller consulting an Agent-tier Expert should ALWAYS wrap
  the call in its own `try/except`, even when the Expert itself already
  returns an honest `{"status": "unavailable", ...}` dict on its own known
  failure mode** — the wrapper's job is guaranteeing the PIPELINE never
  crashes on ANY exception the Expert might raise, not just the one
  failure mode the Expert already handles gracefully itself.
- **A scoped, disclosed monkeypatch-of-the-model-factory stub (engineered
  JSON replies) proved directly reusable a second time** (first
  `REQ-SB-63-US-01-T01`, then `T02`) for deterministically engineering a
  specific Expert decision outcome without depending on a real model's own
  non-deterministic phrasing.

### Antipatterns (avoid this)

- **Do not assume a task file's own illustrative example values (a `kind`
  name, a customer name) are literally present in a fresh scratch vault**
  — verify what the scratch vault's own seeded state actually contains
  before engineering a test decision against it. A fresh scratch vault's
  `known_kinds` is whatever the test itself has created so far, not
  whatever a task's prose happens to name as an example.

### Sizing calibration

- **Estimated:** ~3 tasks, S — **Actual:** 3 tasks, S — exact match, the
  THIRD consecutive time this "~3 tasks, S, generalize/extend an
  already-Done Expert module" shape has landed precisely on estimate
  (`SPRINT-023`, `SPRINT-024`, now `SPRINT-050`) — a reliable sizing
  anchor for future single-Expert-generalization stories.
