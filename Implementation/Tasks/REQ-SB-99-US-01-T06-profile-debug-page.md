---
id: REQ-SB-99-US-01-T06
title: The profile debug page — route, API client, five regions, honest failures, and the way in from the agent panel
parent_story: REQ-SB-99-US-01
requirement_id: REQ-SB-99
type: frontend
status: Done
gate: flagged
gate_reason: "Scope-internal judgement calls logged for human spot-check — the breadcrumb's middle crumb is the profile id (the profile folder name) rather than a display name, so the page costs no second fetch; a region-level failure and a config-LAYER-level failure get two different test ids (`profile-config-error` / `profile-config-layer-error`); the toolsets block renders outside the config region's read-guard so one cannot hide the other; one honest caveat sentence was added where a layer is unreadable, because the backend labels a key found in the one readable layer as `install_root` without saying the other file might set it too. Plus one out-of-scope FINDING raised to REVIEW-QUEUE.md about that backend label. `MEMORY.md` deliberately not appended to — the file is 86 KB against its own 40 KB budget and its rule 1 forbids appending. Nothing blocked; no AC weakened."
phase: P2
depends_on: [REQ-SB-99-US-01-T05]
created: 2026-10-17
updated: 2026-10-18
---

# REQ-SB-99-US-01-T06 — A Page You Can Paste Into an Incident Note

## Parent Story

- Story: [[REQ-SB-99-US-01]] — `../UserStories/REQ-SB-99-US-01-hermes-profile-as-it-really-is.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-99 *See a Hermes Profile As It Really Is — Soul, Skills, Config, Jobs*

---

## Objective

Put `T05`'s composed read on its own read-only page, reached from the agent
panel and addressable by URL, rendering five regions and the three failure
kinds exactly as the backend reports them.

---

## Starting State → End State

**Before / Inputs:**

- `T05` serves `GET /hermes/agents/{agent_id}/profile-detail`.
- `src/frontend/src/App.tsx` declares one flat `<Route>` per page under
  `AppShell`; pages live in `src/frontend/src/pages/`.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` is the agents-map
  API client (`fetchAgent`, `fetchAgentJobs`, … ) — the new call belongs here.
- `src/frontend/src/components/Breadcrumbs.tsx` (`ADR-042`) renders the trail;
  the last crumb is never a link.
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` has seven tabs
  that fetch on mount; its overview tab already carries a navigation link
  precedent (`data-testid="overview-chat-link"`).
- The live approved families are `.item-list` / `.item-row` /
  `.item-row-main` / `.item-row-title` / `.item-row-meta`, `badge`, `kv-row`
  and `.empty-state`.
- The frontend has **no test runner** (it does not declare `vitest`), so this
  task verifies structurally in a real browser.

**After / Outputs:**

- `src/frontend/src/pages/HermesProfileDetailPage.tsx` (new) — route
  `/agents/:agentId/profile`, rendering five regions, each with its own
  `data-testid`:
  - `profile-soul-region` — the full soul in one `<pre>`-style verbatim block
    (`data-testid="profile-soul-text"`), never excerpted, never reassembled.
  - `profile-skills-region` — one `.item-row` per skill
    (`data-testid="profile-skill-row"`) carrying the deployed version and a
    `badge` with its verdict, including `unknown_to_framework`.
  - `profile-config-region` — one row per config key
    (`data-testid="profile-config-row"`) showing the value, the source label
    (*set here* / *inherited from the install root* / *not set*) and the file
    it came from; the two layers are shown as two labelled layers, never merged.
    The enabled toolsets render here as `data-testid="profile-toolset-row"`.
  - `profile-jobs-region` — the profile's own jobs
    (`data-testid="profile-job-row"`) with schedule and last-run outcome, and a
    separately labelled install-level group
    (`data-testid="profile-install-job-row"`).
  - Each region renders a per-region failure element
    (`data-testid="profile-<region>-error"`) when the backend reports one, and
    `.empty-state` only for a genuinely-read empty region.
- A whole-page unread state (`data-testid="profile-install-error"`) when the
  install itself could not be read — no region rendered as if read.
- Breadcrumbs: Agents → *<profile name>* → Profile detail.
- `src/frontend/src/features/agents-map/agentsApiClient.ts` — one typed
  `fetchHermesProfileDetail(agentId)`.
- `src/frontend/src/App.tsx` — one route.
- `AgentDetailPanel.tsx` — **only the way in**: one link
  (`data-testid="overview-profile-detail-link"`) on the overview tab for a
  Hermes-backed agent, navigating to the page. No new fetch on panel mount.

---

## Files to Modify

- `src/frontend/src/pages/HermesProfileDetailPage.tsx` (new)
- `src/frontend/src/features/agents-map/agentsApiClient.ts` (one call + its types)
- `src/frontend/src/App.tsx` (one route)
- `src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (the link only)

---

## Constraints

- Inherits from parent story.
- **Read-only screen.** No edit control, no save, no deploy, no job action
  anywhere on this page; opening or refreshing it writes nothing.
- **The panel must not pay this page's cost**: no `profile-detail` fetch on
  `AgentDetailPanel.tsx` mount, and nothing added to the Agents Map's
  mount-time fetches (`BUG-086`).
- **Functional-first on approved conventions** (story Notes → Prototype
  parity): reuse `.item-list`/`.item-row`, `badge`, `kv-row` and
  `.empty-state`; introduce no new visual system. Visual polish is an
  out-of-band spot-check against the prototype, never a locked AC.
- Every assertion below is on **DOM structure** — jsdom and a headless browser
  see no computed CSS, layout, colour or `:hover`.
- **Render the backend's own words.** A failed region shows the message `T05`
  returned, naming the file; the screen never invents wording, never
  substitutes an empty list for a failed read, and never shows an excerpt where
  the full soul belongs.
- The soul block preserves whitespace and line breaks exactly as served.

---

## Tests

**Manual verification steps** (real backend on `127.0.0.1:8001` + `npm run dev`;
headless-Edge/CDP screenshot and DOM reads are this project's established
technique — read the DOM back at least ~500ms after any dispatched state
change; check the backend's CORS allow-list before picking a frontend port):

1. `[REQ-SB-99-US-01-AC-01]` Open the Agents Map, open a real Hermes agent's
   panel, click `[data-testid="overview-profile-detail-link"]`, and confirm it
   routes to `/agents/<id>/profile`. Assert
   `[data-testid="profile-soul-text"]`'s text equals the profile's real
   `SOUL.md` on disk byte-for-byte (read the file to compare), is longer than
   280 characters, and shows the `## Scope` body and section order. Confirm the
   Agents Map still shows that agent's existing short description unchanged.
2. `[REQ-SB-99-US-01-AC-02]` Confirm one
   `[data-testid="profile-skill-row"]` per skill in that profile's own
   `skills/` tree, each showing its deployed version and a verdict `badge`.
   Copy one skill folder into the profile under a slug the framework's catalog
   does not have, reload, and confirm it renders as a row with an
   unknown-to-framework badge rather than being omitted; remove it again.
3. `[REQ-SB-99-US-01-AC-03]` Confirm `[data-testid="profile-config-row"]`
   entries render the two layers as two labelled layers — each value naming its
   source file, a root-only key labelled *inherited from the install root*, a
   key in neither labelled *not set* — with no single merged "effective" value
   anywhere on the page. Confirm the model, the provider and the enabled
   toolsets (`[data-testid="profile-toolset-row"]`) are present.
4. `[REQ-SB-99-US-01-AC-04]` On a profile with its own `cron/jobs.json`,
   confirm `[data-testid="profile-job-row"]` lists exactly those jobs with
   schedule and last-run outcome, that a job living only at the install root
   appears **only** in the install-level group
   (`[data-testid="profile-install-job-row"]`), and that the Hermes Ops cron
   screen still lists exactly what it listed before.
5. `[REQ-SB-99-US-01-AC-05]` Snapshot `<HERMES_HOME>` (recursive path → sha256
   + mtime, PowerShell) before opening; open the page, refresh it, navigate
   away and back; re-snapshot and confirm the two are identical. In the same
   session, confirm via a `window.fetch` spy that the page issues exactly one
   `profile-detail` request per load and that opening the agent panel alone
   issues none.
6. `[REQ-SB-99-US-01-AC-06]` Temporarily rename that profile's `SOUL.md` and
   break its `config.yaml`, and induce a toolsets read failure (the established
   in-process monkeypatch of `HermesCLI._run` against the real running app).
   Confirm the page renders the missing file by name in
   `[data-testid="profile-soul-error"]`, the unreadable config file by name,
   and a toolsets **read-failure** message — explicitly not an empty
   "no toolsets enabled" state — while the skills and jobs regions still render
   their real content. Restore every file and confirm the page returns to its
   read state.
7. `[REQ-SB-99-US-01-AC-07]` Point the backend's Hermes home at a path that
   does not exist, restart it, and confirm the page renders
   `[data-testid="profile-install-error"]` naming why, and that **no**
   region-level content element (`profile-skill-row`, `profile-config-row`,
   `profile-job-row`, `profile-soul-text`) is present in the DOM. Restore the
   real path.

**Automated tests:** `n/a — the frontend declares no test runner (CLAUDE.md:
"no tests and does not declare vitest"); verified structurally in a real
browser as above. The backend behaviour behind every step above is pinned by
T05's pytest suite.`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] A dedicated, addressable read-only page with the five regions
- [x] Breadcrumbs trail and a way in from the agent panel's overview tab
- [x] Per-region failures and the whole-install failure rendered in the
      backend's own words
- [x] No new fetch on panel mount or on any listing path
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
      — **not updated, deliberately.** The rule this task would have written
      (`.empty-state` means "read and empty"; a failed read never borrows it)
      is new and reusable, but `MEMORY.md` is 86 KB against the 40 KB budget
      its own rule 1 sets, and that rule forbids appending while over budget
      unless the new entry REPLACES one it supersedes. This one supersedes
      nothing. It is written in the retro's *Patterns to carry forward*
      instead, which is the harvesting route the human owns.
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Editing anything from this view — soul, config, skills or jobs.
- Reworking the Agents Map, the agent panel's seven tabs, or
  `agents_map_adapter.py`.
- Session transcripts — `REQ-SB-100-US-01`.
- A cross-profile comparison table — `REQ-SB-96-US-01`.
- Visual polish beyond reusing the approved families (out-of-band spot-check).

---

## Context / Notes

`architecture.md` → **§Surface — a Page, Not an Eighth Tab** and `ADR-043`: a
dedicated route and page, because this view is deliberately expensive and worth
a URL that can be pasted into an incident note; the panel gains only the way in,
and `ADR-042`'s breadcrumbs give the way back. The story's Notes record the
operator's 2026-08-31 functional-first precedent — compose from already-approved
families now, visual pass afterwards.

---

## Implementation Log

**2026-10-18 — Done.** Four files, exactly the four in `## Files to Modify`:
`src/frontend/src/pages/HermesProfileDetailPage.tsx` (new, the page),
`src/frontend/src/features/agents-map/agentsApiClient.ts` (+1 call, its types
and one type import), `src/frontend/src/App.tsx` (+1 route), and
`src/frontend/src/features/agents-map/AgentDetailPanel.tsx` (the link and its
`Link` import, nothing else). No backend file was touched.

**File-list check, run before any code was written** (the standing rule,
`MEMORY.md`: *what single edit, in a file this task does not otherwise touch,
is the difference between this code existing and this code running?*). The
switch-on site is the `<Route>` in `App.tsx` and `App.tsx` **is** in the list,
so nothing else needed authorising and no escalation was raised. The route is
reachable from `AgentDetailPanel.tsx` (also listed) and `Breadcrumbs.tsx` is
imported but not modified. No CSS file is needed: every class used
(`.item-list`/`.item-row`/`.item-row-main`/`.item-row-title`/`.item-row-meta`,
`badge`/`badge-success`/`badge-warning`/`badge-danger`, `kv-list`/`kv-row`/
`kv-key`, `.empty-state`, `.card`, `.mono`, `.text-muted`) already exists.

### What was built

- **Route `/agents/:agentId/profile`**, one page, strictly read-only — the DOM
  check below found **zero** `button`/`input`/`textarea`/`select` elements in
  the page body.
- **Five regions**, each with its own test id: `profile-soul-region` (the soul
  in one `<pre>`, `profile-soul-text`, never excerpted),
  `profile-skills-region` (`profile-skill-row` + a verdict `badge`),
  `profile-config-region` (two labelled layer blocks, `profile-config-row` per
  key, `profile-toolset-row` per toolset), `profile-jobs-region`
  (`profile-job-row` for this profile's own, `profile-install-job-row` for the
  install-level group), and the whole-page `profile-install-error`.
- **Honest absence preserved end to end.** Every region's payload is typed
  `| null`, and the three states are three different renderings: a failed read
  is a `Could not be read` element carrying the backend's own message verbatim;
  `.empty-state` is used **only** where `read` is true and the payload is
  genuinely empty; an unreadable install renders no region at all, not even a
  region wrapper.
- **The panel's only change is the way in** — `overview-profile-detail-link`, a
  `<Link>`, shown for `provider_id === 'hermes'` (`agent.managed_by`, which is
  `null` for a Pipeline). It fetches nothing.

### Verification — manual mode, in a real headless browser, every locked AC

The frontend declares no test runner, so every assertion below is on the real
DOM of the real page, read over CDP ≥500 ms after the state it describes, with
screenshots reviewed (not merely captured). Two environments were used and both
are named per AC:

- **LIVE** — the operator's own backend on `:8001` and dev server on `:5173`,
  against the real Hermes install. Read-only pages only; nothing was written.
- **DISPOSABLE** — a throwaway backend on `:8023` and a second Vite on `:5174`
  (`VITE_API_BASE_URL` overridden), over a scratch Hermes home, scratch vault
  and scratch data path, all under this session's scratchpad. Everything
  destructive (renaming a `SOUL.md`, breaking a `config.yaml`, adding and
  removing a skill folder, pointing the home at a path that does not exist)
  happened only here. The operator's `:8001` answered `200` before and after
  every step.

| AC-ID | Where | Observed |
|---|---|---|
| `AC-01` | LIVE | Opened `/?agent=adnoc-expert`, clicked `[data-testid="overview-profile-detail-link"]` → routed to `/agents/adnoc-expert/profile`. `profile-soul-text` holds **5598** characters; `sha256` of its `textContent` is `4b75e696035e699da1dc55996d27ab2f46e591a92e2500b4c332803f6caa5b20`, **equal** to `sha256(SOUL.md read exactly as the backend reads it)` — `Path.read_text(encoding="utf-8")`, i.e. universal-newline mode; the file on disk is CRLF (5701 raw bytes) and that translation happens in `_read_file_as_written`, documented there, not on this page. 5598 > 280. Section order rendered verbatim: `## Your knowledge is live, never cached` → `## You are read-only` → `## What you're for` → `## Scope boundary` → `## Your preferred indexes` → `## What this app can do` → `## Guardrails` → `## Scope`, with `## Scope`'s prose body present. Breadcrumbs `Agents › adnoc-expert › Profile detail`, last crumb not a link. The Agents Map panel still shows the same short description, *"Customer Expert for ADNOC -- read-only specialist on that single customer's real vault data (Opportunities, People, engagement history)."* — the real 136-character `description`, not the soul. **Pass.** |
| `AC-02` | LIVE + DISPOSABLE | LIVE `adnoc-expert`: **66** `profile-skill-row`s — one per skill in that profile's own `skills/` tree — each with its deployed version and a verdict badge; verdict counts `unknown to the framework` 63 (adnoc) / 62, `modified` 1, `current` 3. DISPOSABLE: copied `vault-index/SKILL.md` into the profile as `vault/not-a-framework-skill` at version `7.7.7`, reloaded → it renders as a row reading *"vault/not-a-framework-skill · unknown to the framework · deployed version 7.7.7 — framework catalog has no skill with this slug"*, **not omitted**; removed it again and the page went back to the single `vault/vault-index · stale · deployed 0.0.9 / catalog 0.1.0` row. **Pass.** |
| `AC-03` | LIVE + DISPOSABLE | Two layer blocks in both: *This profile's own config.yaml* and *The install root's config.yaml*, each naming its real file. LIVE `azure-expert`: `model.default "gpt-5"` and `model.provider "custom"` present; `command_allowlist` renders **inherited from the install root** with only the root file named; 110 key rows, badge-combination counts `set here \| inherited from the install root \| set in more than one layer …` ×109 and `inherited from the install root` ×1; 25 `profile-toolset-row`s. DISPOSABLE (fixture designed to produce every label): `agent.reasoning_effort` → **not set**; `model.provider` / `logging.level` / `command_allowlist` → **inherited from the install root**; `model.default` → `"gpt-5-profile"` *set here* **and** `"gpt-5-root"` *inherited from the install root*, two genuinely different values side by side, badged *"set in more than one layer — both are shown, neither is presented as the one in effect"*. A full-body regex for "effective value" matched exactly one string on the page: the sentence saying none is produced. **Pass.** |
| `AC-04` | LIVE + DISPOSABLE | LIVE `azure-expert`: exactly **one** `profile-job-row`, `azure-kb-refresh`, *"every 20160m — last run never"* — which is exactly the one job in `profiles/azure-expert/cron/jobs.json` on disk; the 12 root-only jobs appear **only** as `profile-install-job-row`, each with schedule and last-run outcome, and none of them in the profile's own list. LIVE `default` (the primary profile IS `<HERMES_HOME>`): 12 own job rows, **0** install-level rows and the explicit line *"This profile IS the install root, so the jobs above are the install-level jobs. They are not listed a second time here."* — not a misleading empty list. Regression: `GET /hermes/cron/jobs` returns the same 12 names, and the Hermes Ops cron screen (`/crawlers`) renders exactly those same 12 rows in the same order. **Pass.** |
| `AC-05` | DISPOSABLE (filesystem) + LIVE (fetch spy) | Snapshot of the whole scratch `<HERMES_HOME>` — every file and directory, relative path → sha256 + mtime + size, 14 entries — taken before and after **open → refresh → navigate away to `/crawlers` → navigate back**: **identical**, nothing created, nothing removed. A `window.fetch` spy installed via `Page.addScriptToEvaluateOnNewDocument` (before any app code runs) counted `profile-detail` requests per load: open **1**, refresh **1**, away **0**, back **1**. LIVE: opening the agent panel alone (`/?agent=adnoc-expert`, 24 requests in total) issued **0** `profile-detail` requests. The unreadable-install run also left its absent directory absent. **Pass.** |
| `AC-06` | DISPOSABLE | One page view, with `SOUL.md` renamed away, `config.yaml` replaced by invalid YAML, and the toolsets subprocess genuinely failing: `profile-soul-error` names the missing file (*"No such file or directory: …\profiles\debug-profile\SOUL.md"*) and **no** `profile-soul-text` and **no** `.empty-state` in that region; the profile config layer renders *Could not be read* with its own path and the real parser message (*"… is not valid YAML: while parsing a flow sequence …"*) while the **install-root layer still shows its 3 real keys**; `agent.reasoning_effort` changes from *not set* to *unknown — a config layer could not be read*; the toolsets block renders *Could not be read* plus the CLI's own words (*"Error: Profile 'debug-profile' does not exist…"*) with **0** `profile-toolset-row`s and no "nothing enabled" wording anywhere on the page; the skills region still shows `vault/vault-index stale` and the jobs region still shows both `debug-profile-own-job failed` and `root-only-job ok`. Restored both files → the page returned to its read state (soul 2220 chars, both layers `read`, five key rows with their original labels), and the file snapshot matched the pre-break one on every file hash (only the profile directory's own mtime differed, from my rename). **Pass.** |
| `AC-07` | DISPOSABLE | Restarted the backend with `HERMES_HOME_PATH` pointing at a directory that does not exist. The page renders `profile-install-error` carrying the backend's own sentence naming the path (*"The Hermes install at …\there-is-no-hermes-install-here is not a readable directory"*). `profile-skill-row` 0, `profile-config-row` 0, `profile-toolset-row` 0, `profile-job-row` 0, `profile-install-job-row` 0, `profile-soul-text` 0, `.empty-state` 0 — and not even a region **wrapper** (`profile-soul-region` / `-skills-region` / `-config-region` / `-jobs-region` all absent), so nothing can read as a region that was read and found empty. The absent directory was still absent afterwards. Restarted onto the real fixture path and the page came back. **Pass.** |

### Gates

- `pytest -q` in `src/backend`: baseline **618 passed** at `78fb600`, final
  **628 passed, 0 failed, 49.03s**. The +10 are another session's
  (`REQ-SB-95-US-04-T02`, commits `d71630f` / `0add57d`, landed mid-session);
  this task touched no backend file. Both named flakes passed in both runs.
- `npx tsc --noEmit` from `src/frontend`: **clean, exit 0**. No shared union was
  widened, so no exhaustive `Record<Union, …>` was put out of date — the new
  lookup maps are `Record<string, string>` with an explicit fallback that
  renders an unrecognised verdict/source as itself rather than dropping it.
- `npx oxlint src`: **12 warnings, all pre-existing, 0 in these four files**,
  0 errors.

### Judgement calls (scope-internal — `gate: flagged` for spot-check)

1. **The middle breadcrumb is the profile id, not a display name.** The task
   says *Agents → <profile name> → Profile detail*, and `profile-detail`'s
   response carries `profile_id` and no name. The profile id **is** the profile
   folder name, which is what an operator pastes into an incident note; fetching
   `GET /agents/{id}` purely for a prettier crumb would add a second request to
   a page whose whole cost story is "one composed read". The crumb links to
   `/?agent=<id>`, the map's own existing deep link.
2. **Two different test ids for two different config failures.** The config
   *region* failing is `profile-config-error`; one config *layer* failing while
   the region itself produced is `profile-config-layer-error`. They are
   genuinely different facts and the second is the one `AC-06` exercises;
   giving both the same id would make a layer failure look like a region
   failure.
3. **The toolsets block sits outside the config region's read-guard**, inside
   the same visual card. They are two independent regions on the backend (a
   subprocess versus two file reads), and nesting the toolsets inside
   `config.read` would let an unreadable `config.yaml` silently hide a perfectly
   good toolsets read — the exact coupling this story exists to remove.
4. **One caveat sentence added for a partially-read config**
   (`profile-config-partial-read-warning`). See the finding below: with one
   layer unreadable, a key found in the other is labelled *inherited from the
   install root*, which is true about what was read and not true about the
   profile. Rather than relabel the backend's answer (inventing), the page
   states the limit once, above the key list, and only when a layer really
   failed. Confirmed absent when both layers read.
5. **`.empty-state` is never used for a failure.** The story calls
   `.empty-state` the "honest-failure convention", but this task's own
   constraint says `.empty-state` is for *a genuinely-read empty region*. A
   failed read gets its own element carrying a `badge-danger` label and the
   backend's verbatim message. Where the two would collide, the narrower rule
   won.
6. **`<Link className="btn">` is left underlined.** `.btn` sets no
   `text-decoration`, so every `Link className="btn"` in this app renders
   underlined (five existing precedents). Overriding it inline here would make
   this one control inconsistent with all of them, and the fix belongs in
   `settings.css`, which is not in this task's list.
7. **`MEMORY.md` deliberately not appended to** — see the Acceptance Criteria
   note above.

### Out-of-scope finding (not fixed here — raised in `REVIEW-QUEUE.md`)

`profile_detail.py::_config_key_rows` labels a key found in exactly one layer
with that layer's own name, **even when the other layer could not be read**. On
the three-failures page the operator sees `model.default → "gpt-5-root"
inherited from the install root`, while the profile's own `config.yaml` — the
unreadable one — does in fact set it to `"gpt-5-profile"`. The adjacent
`not_set`-vs-`unknown` rule already covers the case where *no* layer has the
key; this is the same hazard one step over. It is a `Done` task's backend
semantics and outside this task's files, so nothing was changed: the page
states the limit in its own words instead, and the decision is the human's.

### Second observation, not a defect of this task

The disposable backend's own startup Action-catalogue publication **rewrote**
the fixture `profiles/debug-profile/SOUL.md` (1001 → 2220 bytes, appending a
`## What this app can do` block). That is `T05`'s already-raised finding seen
again, here in its milder appending form — `## Scope` survived. It did not
affect any assertion above (every snapshot was taken after startup settled),
and nothing new is filed for it.
