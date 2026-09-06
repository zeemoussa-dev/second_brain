# Retired MEMORY.md entries

The 7 entries retired on 2026-09-05, each with the reason. Kept, never deleted.

Verbatim from `MEMORY.md` as it stood on 2026-09-05. Nothing edited.

---

## Entry 046  (Decisions section, 1249 chars)

> **Why retired:** Superseded by entry 047, which added the `body` parameter that made this limitation obsolete.

- **[2026-09-01 Constraint]** `REQ-SB-87-US-02-T01` could NOT migrate RawMessage creation itself onto `vault_manager.py`'s `create_dynamic_child()` — confirmed live and blocking, not just the theoretical gap `REQ-SB-87-US-01-T05` had already flagged. `create_dynamic_child()`'s own `body_parts` construction iterates ONLY the dynamic child's own declared `Template.json` `sections` list; the real `thread/Template.json`'s `messages` child declares none, so every RawMessage created through it today gets a genuinely EMPTY body — any caller-supplied `sections` dict content is silently dropped, not even a partial write. Closing this needs a file outside this task's own `## Files to Modify` either way: declaring a `"Body"` section on the Thread template's `messages` child (edits `T05`'s own already-`Done`, live `Template.json`) or extending `create_dynamic_child()` itself (the CANONICAL `Hermes-Provisioning/shared/vault_manager.py`, then re-deploying to all 82 real active copies — a genuine engine-contract, architecture-level change, not a local coder call). Escalated (`ESC-061`); `REQ-SB-87-US-02-T01` marked `Blocked`, not `Done` — its own `AC-01` can't be verified as fully passing until this is resolved, `AC-02` does pass live as built.

## Entry 094  (Constraints section, 2088 chars)

> **Why retired:** Superseded - `chat_sessions.py` added persistent per-agent sessions, as entry 017 records.

- **[2026-08-23] `POST /agents/{agent_id}/chat` (`agents_router.py`) is a genuinely stateless, one-shot REST turn — it opens a fresh `HermesChatSession` per HTTP call and closes it in `finally`, with no session/`request_id` continuity held across separate calls.** This means it can surface a `clarify.request`/`approval.request` event's question/approval text AS the turn's own reply (fixed 2026-08-23 — previously it silently blocked for the full `_CHAT_TURN_TIMEOUT_S`/180s and 504ed, found while verifying the new `azure-calculator` agent's real clarifying-question behavior through this same endpoint), but it can NEVER actually answer one via `clarify.respond`/`approval.respond` — there is nowhere to hold the request's own `request_id` open for a follow-up HTTP call to resolve. This is acceptable because Hermes' own gateway already tolerates an unanswered clarify/approval past its own configured timeout (confirmed live: falls back to locked/default answers and the agent continues on its own — the same "(clarify timed out after 120s — locked answers returned)" fallback observed in this session's one-shot CLI test of `azure-calculator`), so the worst case is a slightly stale continuation, never a hang. Real wire shapes confirmed directly against the installed `hermes-agent` source (`tui_gateway/server.py::_block`/`_clarify_block`/`_emit_approval_request`): `clarify.request` carries `question` (single) or `questions` (batch, each `{question, choices, multi_select}`); `approval.request` carries `command` and optional `reason`; both carry the request's own `request_id`, but Second Brain's REST endpoint has no use for it today. General lesson: a genuine multi-turn clarify/approval answer flow through this endpoint would need session continuity across HTTP calls (e.g. keep the `HermesChatSession` alive keyed by a conversation id, or route a follow-up message to `clarify.respond` when one is pending) — real, scoped future work if this becomes a frequent UX complaint, not attempted here since the fallback already makes the current behavior honest and non-hanging.

## Entry 098  (Constraints section, 862 chars)

> **Why retired:** Exact duplicate of entry 070, which is kept.

- **[2026-08-24] Hermes' own `cron create <schedule>` CLI arg needs a literal `"every "` prefix to register a REPEATING job — a bare `"20160m"` (no prefix) registers a ONE-TIME job that fires once after that delay, not a recurring one, with no error or warning distinguishing the two at creation time.** Found live registering the Compass KB refresh cron job: `hermes cron create "20160m" ...` silently created a job whose OWN listing showed "Schedule: once in 20160m" (not "every 20160m" the way every other real cron job in this install shows) -- caught only by comparing the listing output against a known-good existing job (`new-company-discovery`, "every 1440m"), not by any error. Always `hermes cron list` immediately after `cron create` and confirm the schedule string literally says "every", not "once in", before trusting a new job will actually recur.

## Entry 105  (Constraints section, 775 chars)

> **Why retired:** Merged into the surviving port-8001 rule; its unique detail (empty UI, no console cause) was carried across.

- **[2026-08-25, CORRECTED 2026-09-04] The backend serves port **8001**, not 8000, and a mismatch shows up as a completely empty UI with no console-visible root cause beyond the network tab.** Originally this depended on `src/frontend/.env.local` pinning `VITE_API_BASE_URL=http://127.0.0.1:8001`, which was load-bearing AND uncommittable (`src/frontend/.gitignore`'s `*.local`) -- so a fresh clone silently fell back to 8000 and rendered a black page. Fixed 2026-09-04: the six source defaults now say 8001, matching the port `tools
un-backend.cmd` actually serves, and `.env.local` is a genuine override again rather than a prerequisite nobody can receive. The empty-UI symptom is the thing worth remembering -- it points at the API base URL, not at the backend being down.

## Entry 148  (Constraints section, 1029 chars)

> **Why retired:** Duplicate of entry 033, which routes to instance memory.

- **[2026-09-02 Constraint] The sandboxed Bash tool's own shell environment can have a non-functional `python`/`py` PATH entry (Windows' `WindowsApps\python.exe` App Execution Alias stub, "Python was not found; run without arguments to install from the Microsoft Store") even when a real Python IS installed on the host and resolvable from a normal PowerShell session.** Found live, `REQ-SB-87-US-03-T01`: `python derive_noise_definition.py ...` via the Bash tool exited 49 with that exact message; the SAME machine's PowerShell `Get-Command python` and `py -0p` both resolved a real interpreter (`AppData\Local\Python\pythoncore-3.14-64\python.exe`). When a script invocation needs a real Python in a Bash-tool call on this host, resolve the real interpreter path first via PowerShell (`py -0p`, or `Get-Command python`) rather than trusting a bare `python`/`py` call to work — the same class of finding already documented for `npx`/`node`/`npm` (`Implementation/Learnings.md`, `SPRINT-027`/`028`), now confirmed for Python too.

## Entry 175  (Constraints section, 777 chars)

> **Why retired:** Marks itself SUPERSEDED 2026-09-04.

- **[2026-09-03, SUPERSEDED 2026-09-04] `_FALLBACK_SECTION_NAME = "Data Gatherer"` no longer exists in `agent_manager.py`.** It used to resolve an unplaced agent to that Section and CREATE it when absent, which meant a clean build could not stay Section-free: Primary is mirrored from Hermes on every `GET /agents`, so deleting every Section silently undid itself on the next read. `_section_id()` returns `None` now (`Agent.section_id` was always `str | None`), and `section_manager` no longer seeds a starting six -- Sections come only from an explicit human action. **Still live:** `pipeline_manager._section_id_by_name()` creates a Section named by a Pipeline's own data; it cannot fire without Pipelines, and closing it would need `Pipeline.section_id` to become optional.

## Entry 177  (Constraints section, 1360 chars)

> **Why retired:** Marks itself TRANSIENT and external to this project.

- **[2026-09-03 Constraint, found live, confirmed TRANSIENT -- external to this project] `hermes profile import` failed for a real Agent with `PermissionError: [WinError 5] Access is denied` during its own rename-after-extract step** (`hermes_cli/profiles.py`, `extracted.rename(final_source)`), confirmed live twice (both `notes-manager` and `files-manager`, real import via the new Artifacts import UI, `keep_both` decision). **Retried directly the same day (operator: "Retry the import to see if the Hermes permission error was transient") -- both `notes-manager` and `files-manager` (the larger, 36MB one included, ruling out the size-correlation theory) succeeded cleanly on a plain `hermes profile export`/`import` retry, no code changes.** Root cause not fully diagnosed, but confirmed a real, one-off Windows file-lock (most likely antivirus/indexing scanning a freshly-extracted temp folder before the rename could happen) rather than anything structural. This is Hermes' own external CLI/environment issue, not something this project builds or can fix directly (`MEMORY.md`'s own standing rule: "Hermes is an external integration point"). **Relevant to the CBO handoff** -- the same failure could recur on his machine; if it does, simply retrying the import is the correct, already-confirmed fix, not a sign the `.sbf` bundle or import code is wrong.
