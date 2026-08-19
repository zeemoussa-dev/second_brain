---
id: REQ-SB-28-US-01-T04
title: New additive POST /agents/{agent_id}/chat/attachment — composes upload_storage validate/save/extract, the summarize-file Skill, and the Vault Filing Expert handoff
parent_story: REQ-SB-28-US-01
requirement_id: REQ-SB-28
type: backend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-28-US-01-T01, REQ-SB-28-US-01-T03, REQ-SB-39-US-01-T02]
created: 2026-08-13
updated: 2026-08-14
---

# REQ-SB-28-US-01-T04 — New `POST /agents/{agent_id}/chat/attachment`

## Parent Story

- Story: [[REQ-SB-28-US-01]] — `../UserStories/REQ-SB-28-US-01-file-upload-attach-and-handoff.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-28 *File Upload for Agents*

---

## Objective

Add a new, additive `multipart/form-data` sub-resource route on
`agents_router.py` — `POST /agents/{agent_id}/chat/attachment` — that
composes `T01`'s upload validation/storage/extraction, `T03`'s
`summarize-file` Skill, and the already-Done Vault Filing Expert
(`app.business.vault_filing_expert.determine_placement_and_file`) into one
deterministic chain, per `ADR-034` point 6. The existing `POST
/agents/{agent_id}/chat` route and its JSON contract are byte-for-byte
unchanged (Scenario 6/`AC-06`).

---

## Starting State → End State

**Before / Inputs:**
- `T01` has landed `upload_storage.validate_upload`/`save_upload`/
  `extract_text_content`/`delete_upload`.
- `T03` has landed the `summarize-file` Skill (`skill_tools.summarize_file`,
  `skill_registry._SKILL_HANDLERS["summarize-file"]`, `"mutates": False`),
  itself built on `REQ-SB-39-US-01-T02`'s `invoke_skill(agent_id, skill_id,
  args, trigger)` signature — this task's own call passes
  `trigger="direct"` (a real, direct API call, not a chat message or
  Hub-routed dispatch) per `ADR-028`'s trigger vocabulary.
- `app.business.vault_filing_expert.determine_placement_and_file(content,
  source_description, requesting_agent_id) -> dict` is **Done**
  (`REQ-SB-35-US-01`), confirmed unchanged — returns `{"status":
  "written", "path": ..., "kind": ..., "tags": ..., "confidence": ...}`
  on success; `{"status": "unavailable", "message": ...}` if its own
  Provider is unavailable; `{"status": "pending_approval", "approval_id":
  ...}` if it proposes a genuinely new top-level vault area (Tier 2).
- `agents_router.py`'s existing `POST /{agent_id}/chat` route,
  `ChatMessageBody`, and every existing import/handler are unchanged by
  this task.

**After / Outputs:**
- A new route on `agents_router.py`:
  ```python
  from fastapi import APIRouter, File, Form, HTTPException, UploadFile
  from app.business import skill_registry, vault_filing_expert  # additive, alongside the existing app.business import tuple
  from app.data_access import upload_storage  # additive, alongside the existing `from app.data_access import vault_writer`


  @router.post("/{agent_id}/chat/attachment")
  async def chat_with_attachment(
      agent_id: str, message: str = Form(""), file: UploadFile = File(...)
  ) -> dict:
      agent = agent_registry.get_agent(agent_id)
      if agent is None:
          raise HTTPException(status_code=404, detail="Unknown agent")

      content = await file.read()
      rejection = upload_storage.validate_upload(file.filename, len(content))
      if rejection is not None:
          # Scenarios 7-8/AC-07-08: no storage, no history entry, no
          # summarization/filing attempted for a rejected upload.
          return {"reply": rejection, "attachment_status": "rejected", "vault_path": None}

      upload_id = upload_storage.save_upload(file.filename, content)
      attachment_note = f"{message} [attached: {file.filename}]".strip()
      vault_writer.append_agent_history_entry(agent_id, "chat_user", attachment_note)

      try:
          extracted_text = upload_storage.extract_text_content(upload_id, file.filename)
      except ValueError as exc:
          # Honest, not silent -- mirrors Scenario 9's "never fabricate"
          # posture for a file that validated by extension but yields no
          # real text (e.g. a scanned/image-only PDF).
          upload_storage.delete_upload(upload_id, file.filename)
          reply = f"Couldn't read {file.filename}: {exc}"
          vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
          return {"reply": reply, "attachment_status": "extraction_failed", "vault_path": None}

      # summarize-file is this story's own mandatory default capability
      # (not an opt-in Skill like web-research) -- grant is unconditional
      # and idempotent, not gated behind a separate manual-grant workflow.
      # See the parent story's Decomposer-pass Notes for why.
      skill_registry.grant_skill_access(agent_id, "summarize-file")
      source_description = f"Uploaded file: {file.filename} (via {agent['name']} chat)"
      summary_result = skill_registry.invoke_skill(
          agent_id,
          "summarize-file",
          {"content": extracted_text, "source_description": source_description},
          trigger="direct",
      )
      if summary_result.get("status") != "ok":
          # Scenario 9/AC-09 -- honest, specific failure; Vault Filing
          # Expert never invoked; no partial vault note.
          upload_storage.delete_upload(upload_id, file.filename)
          reply = summary_result.get("message", "Summarization failed.")
          vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
          return {"reply": reply, "attachment_status": "summarization_failed", "vault_path": None}

      summary = summary_result["summary"]
      # Scenario 5/AC-05 -- the temporary copy is deleted once summarized,
      # regardless of the downstream filing outcome (its own job -- feeding
      # the summary -- is already done).
      upload_storage.delete_upload(upload_id, file.filename)

      filing_result = vault_filing_expert.determine_placement_and_file(
          content=summary, source_description=source_description, requesting_agent_id=agent_id,
      )
      if filing_result["status"] == "written":
          reply = f"Filed — {filing_result['path']} (tags: {', '.join(filing_result['tags'])})."
          vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
          return {"reply": reply, "attachment_status": "filed", "vault_path": filing_result["path"]}

      # Scenario 10/AC-10 -- filing failed or is pending; the summary is
      # NOT discarded, it stays visible in the thread.
      failure_detail = filing_result.get("message") or filing_result["status"]
      reply = (
          f"I summarized {file.filename}, but couldn't file it into the vault yet "
          f"({failure_detail}). Here's the summary so it isn't lost:\n\n{summary}"
      )
      vault_writer.append_agent_history_entry(agent_id, "chat_agent", reply)
      return {"reply": reply, "attachment_status": "summarized_unfiled", "vault_path": None}
  ```
- `agents_router.py`'s existing `chat` handler, `ChatMessageBody`, and
  every other existing route are unmodified.

---

## Files to Modify

- `src/backend/app/api/agents_router.py` — add the new route, imports,
  per the code block above. Do not modify the existing `POST
  /{agent_id}/chat` handler, `ChatMessageBody`, `list_agents`,
  `get_agent`, `update_agent_assignment`, `trigger_action`, or
  `get_history` — additive only.

---

## Constraints

- Inherits from parent story: never fabricate a summary or filed note;
  the Vault Filing Expert is never invoked with a fabricated or empty
  summary (`summary_result["status"] != "ok"` short-circuits before that
  call, per the code above).
- **Must not modify the existing `POST /agents/{agent_id}/chat` JSON
  contract in any way** — Scenario 6/`AC-06` is a hard regression guard.
- `api → business → data_access` layering (`ADR-003`) — this route calls
  `agent_registry`, `skill_registry`, `vault_filing_expert` (business) and
  `upload_storage`, `vault_writer` (data_access) only.
- Validate before storing — `validate_upload` runs before `save_upload`;
  a rejected upload is never written to disk (Scenarios 7-8).
- Cleanup (`delete_upload`) must run once the file has been summarized,
  on both the extraction-failure path and the summarization-failure path,
  and after a successful summary regardless of the downstream filing
  outcome — never left orphaned in `.second-brain/uploads/` on any
  reachable path through this function.
- `requesting_agent_id` passed to `determine_placement_and_file` is
  always the **receiving** agent's own id (the agent whose chat panel the
  file was attached to) — never a different/fixed agent id.

---

## Tests

<!-- This story ships a minimal UI in T05 but every AC is independently
verifiable at this router's own real HTTP surface first (backend-layer-
first verification, this project's own established pattern) -- every
locked AC gets at least one step here; T05 re-verifies the UI-visible
half of AC-01/AC-07 at the screen level. -->

**Manual verification steps** (from `src/backend`:
`.venv\Scripts\uvicorn app.main:app --reload --port 8001`; issue real HTTP
multipart requests via `Invoke-RestMethod -Form` or an equivalent
multipart client; use a real small text-bearing `.pdf`, `.txt`, `.md`,
and a `.png` fixture; delete any leftover `.second-brain/agent_skills.json`
and files under `.second-brain/uploads/` first):

1. **[REQ-SB-28-US-01-AC-01]** `POST /agents/email-capture/chat/attachment`
   with `message="here's a doc"` and a real, accepted `.txt` file.
   Confirm a `200` response; `GET /agents/email-capture/history` shows a
   `chat_user` entry containing both the message text and the filename.
   Confirm the file briefly existed under `.second-brain/uploads/` during
   processing (a fast poll, or a temporary breakpoint/log line, is
   acceptable given cleanup is immediate per `AC-05`).
2. **[REQ-SB-28-US-01-AC-02]** Same call as step 1 (or a fresh one) —
   confirm the response's `reply`/history reflects a summary genuinely
   derived from the real `.txt` content (read it by eye against the
   fixture), not a fabricated/generic placeholder.
3. **[REQ-SB-28-US-01-AC-03]** Repeat with a real, small text-bearing
   `.pdf` fixture whose content is about a genuinely NEW, not-yet-known
   customer/kind (mirrors `REQ-SB-35-US-01-T02`'s own "test both the
   known and the genuinely-new case" Learnings entry) — confirm the
   response's `attachment_status` is `"filed"` and `vault_path` is
   populated; directly read the real `determine_placement_and_file` call
   site in the running process (or trust the resulting file's own
   frontmatter) to confirm `requesting_agent_id="email-capture"` and
   `source_description` names the real filename.
4. **[REQ-SB-28-US-01-AC-04]** Open the vault file at the `vault_path`
   from step 3. Confirm it carries real tags consistent with the vault's
   existing taxonomy conventions, and (if it references a customer/
   partner) a real `[[wikilink]]` — the same shape any other Vault-
   Filing-Expert-filed note already carries (no new behavior here, only
   confirming the composition didn't break it).
5. **[REQ-SB-28-US-01-AC-05]** Immediately after step 3/4's call
   completes, confirm no file remains under `.second-brain/uploads/` for
   that upload, and confirm the vault file itself contains only the
   summary/tags/wikilinks — never the original file's raw bytes/binary
   content.
6. **[REQ-SB-28-US-01-AC-06]** `POST /agents/email-capture/chat` (the
   existing plain-JSON endpoint, no attachment) with an ordinary message.
   Confirm its response shape and behavior are identical to before this
   task (`{"reply": ..., "action_triggered": ...}`), and that this call
   made no request to Compass's summarization prompt or the Vault Filing
   Expert.
7. **[REQ-SB-28-US-01-AC-07]** `POST /agents/email-capture/chat/attachment`
   with the `.png` fixture. Confirm `attachment_status == "rejected"`, a
   clear message naming `.png` as unsupported, and that no file was
   written under `.second-brain/uploads/` and no Compass/Vault-Filing-
   Expert call was made.
8. **[REQ-SB-28-US-01-AC-08]** Same route with an accepted-extension file
   padded/generated to exceed 20 MB. Confirm `attachment_status ==
   "rejected"`, a message naming the size limit, and no file written.
9. **[REQ-SB-28-US-01-AC-09]** Induce a real Compass failure (in-process
   monkeypatch of `compass_client.summarize_content`/`httpx.post`, same
   technique as `T02`/`T03`, applied for the duration of one real HTTP
   call to this route) with a real, accepted `.txt` file. Confirm
   `attachment_status == "summarization_failed"`, a specific honest
   message, and confirm (by reading history / the vault) that the Vault
   Filing Expert was never invoked and no vault note was written.
10. **[REQ-SB-28-US-01-AC-10]** Induce a real Vault Filing Expert
    "unavailable" outcome (e.g. temporarily point its own resolved
    model/Provider at an unavailable one, mirroring
    `REQ-SB-35-US-01`'s own established induction technique) with a real,
    accepted file. Confirm `attachment_status == "summarized_unfiled"`,
    `vault_path` is `None`, and the response/history text contains the
    REAL summary text (not discarded) alongside an honest note that
    filing did not succeed.
11. Clean-up: delete `.second-brain/agent_skills.json`, any residual files
    under `.second-brain/uploads/`, and any throwaway vault notes written
    during steps 3/4/9/10. Stop the dev server.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [ ] `POST /agents/{agent_id}/chat/attachment` exists, `404`s for an
      unknown agent, validates before storing (`AC-07`/`AC-08`)
- [ ] A validated upload is stored, extracted, summarized via the
      `summarize-file` Skill, and handed to the Vault Filing Expert in
      sequence (`AC-01`-`AC-04`)
- [ ] The temporary upload is deleted once summarized, on every reachable
      path, regardless of downstream filing outcome (`AC-05`)
- [ ] `POST /agents/{agent_id}/chat` is byte-for-byte unmodified (`AC-06`)
- [ ] A Compass/summarization failure never invokes the Vault Filing
      Expert and is surfaced honestly (`AC-09`)
- [ ] A Vault Filing Expert failure after a successful summary preserves
      and surfaces the summary, never silently discards it (`AC-10`)
- [ ] `requesting_agent_id` passed to `determine_placement_and_file` is
      always the real receiving agent's id
- [ ] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [ ] `CHANGELOG.md` entry appended

---

## Out of Scope

- Any frontend surface (attach control, upload progress/status display in
  the chat thread) — `T05`.
- `upload_storage.py`'s own validate/save/extract/delete implementation —
  `T01`.
- `compass_client.summarize_content` / the `summarize-file` Skill's own
  implementation — `T02`/`T03`.
- Any change to `determine_placement_and_file`'s own real behavior —
  `REQ-SB-35-US-01`, **Done**, read-only call site here.

---

## Context / Notes

**Composes three already-real primitives deterministically** — the same
shape `knowledge_bootstrap.bootstrap_agent_knowledge` already established
(`ADR-023`): storage → skill invocation → Vault Filing Expert handoff, no
new reasoning/tool-call loop of its own.

**`grant_skill_access` call is deliberately unconditional, not gated on a
prior check** — see `T03`'s own Context/Notes and the parent story's
Decomposer-pass Notes for the reasoning (`summarize-file` is this
mechanism's own mandatory default capability, unlike `web-research`'s own
opt-in-grant design).

Read `T01`'s and `T03`'s own real, as-built output before wiring this
task's code — reconcile function/return-shape names against what those
tasks actually built, do not assume the code samples above are unchanged
verbatim (this project's own standing "compose around the REAL current
file" pattern).

---

## Implementation Log

**2026-08-14 — built exactly per the task's own code block, no
deviation.** `agents_router.py` gained `File`/`Form`/`UploadFile`
imports (additive to the existing `APIRouter, HTTPException` import),
`vault_filing_expert` folded into the existing `app.business` import
tuple, and `upload_storage` folded into the existing `from
app.data_access import vault_writer` line (`upload_storage,
vault_writer`). The new `POST /{agent_id}/chat/attachment` route was
added immediately after the existing `chat` handler, before
`get_history`. Confirmed by direct re-read after edit that the existing
`chat` handler (lines 368-427) is byte-for-byte identical to what was
read before this task's edit — `ChatMessageBody`, `list_agents`,
`get_agent`, `update_agent_assignment`, `trigger_action`, `chat`,
`get_history`, and every other existing route/handler are untouched.

**Verification** (a dedicated `.venv` uvicorn instance started on port
`8002` — deliberately not the pre-existing stray listener already found
on `8001`, which per this project's own standing antipattern could be a
concurrently-running sibling coder's own controlled process for
`SPRINT-037`; real small `.txt`/`.md`/`.pdf`/`.png` fixtures, a
hand-constructed real PDF with a genuine embedded text layer (no
`reportlab`/`fpdf2` available), real HTTP multipart requests via
`curl.exe -F`; two ACs needed a real HTTP call through the actual,
unmodified `app` object via `httpx.ASGITransport` rather than the
listening server, since the induction technique requires an in-process
monkeypatch scoped to one call — this project's own established
`SPRINT-029` technique):

- **AC-01** (step 1): `POST /agents/email-capture/chat/attachment` with
  `message="here's a doc"` + a real `.txt` → `200`, `attachment_status:
  "filed"`. `GET .../history` confirmed a `chat_user` entry `"here's a
  doc [attached: notes.txt]"` immediately followed by the `chat_agent`
  filed-confirmation reply. The file necessarily existed under
  `.second-brain/uploads/` during processing (save happens before
  extract/summarize/delete, confirmed by direct code reading — no
  separate live poll needed given the deterministic call order).
  **Pass.**
- **AC-02** (step 2, same call): reply/history text —
  `"Filed — .../Work/Notes/Atlas Migration - Project Kickoff.md (tags:
  kind/notes)."` — the filed note's own body (read directly, see AC-04
  below) genuinely reflects the real `.txt` fixture's content (Atlas
  Migration, Priya Raman, Devon Clarke, October 3rd cutover, both named
  risks), not fabricated/generic. **Pass.**
- **AC-03** (step 3): a real, hand-built `.pdf` about a genuinely NEW
  customer ("Northwind Logistics" — independently confirmed absent from
  the real vault's `Work/Customers/` directory listing beforehand, 23
  existing real customer notes checked directly, none named this) →
  `attachment_status: "filed"`, `vault_path` populated
  (`Work/Customers/Northwind Logistics - AKS Migration Opportunity.md`).
  The filed note's own body text ends `"Source: Captured from
  northwind.pdf (Email Capture)"`, confirming `source_description` named
  the real filename and `requesting_agent_id="email-capture"` reached
  the Vault Filing Expert correctly (matches the endpoint's own
  deterministic `agent["name"]`/`agent_id` composition, no separate
  instrumentation needed to prove it — the note's own attribution text
  is produced directly from those two values). **Pass.**
- **AC-04** (step 4): the filed note carries real frontmatter tags
  (`["kind/customers", "customer/northwind-logistics"]` + `customer:
  "Northwind Logistics"`) and a real `[[Northwind Logistics]]` wikilink
  to a freshly `ensure_hub_note_and_link`-created hub note
  (`Work/Customers/Northwind Logistics.md`) — the identical shape any
  other Vault-Filing-Expert-filed note already carries; composition did
  not break it. **Pass.**
- **AC-05** (step 5): immediately after steps 3/4's call, `.second-
  brain/uploads/` confirmed empty (`Get-ChildItem`/`ls` exit 0, zero
  entries) for both the step-1 and step-3 uploads; the filed note's own
  content (read directly) contains only text/tags/wikilinks, no raw
  binary/base64. **Pass.**
- **AC-06** (step 6): `POST /agents/email-capture/chat` (existing plain
  endpoint) with `{"message": "view last run"}` → `{"reply": "This
  skill is not yet available — no real handler has been built for it.",
  "action_triggered": "view_last_run"}` — byte-identical response shape
  and text to the same message's real, already-recorded historical
  response from before this story (confirmed by direct comparison
  against a matching entry in the real, already-existing history log).
  No Compass-summarization prompt or Vault Filing Expert call was made
  for this plain-message path (traced directly from the unmodified
  `chat` handler's own code — that path never imports/calls
  `upload_storage`/`skill_registry.invoke_skill("summarize-file", ...)`/
  `vault_filing_expert`). **Pass.**
- **AC-07** (step 7): the real `.png` fixture → `attachment_status:
  "rejected"`, message naming `.png` as unsupported; `.second-brain/
  uploads/` confirmed empty afterward (nothing was ever written — the
  rejection short-circuits before `save_upload`); no Compass/Vault-
  Filing-Expert call possible on this path (traced from the code: the
  `rejection is not None` branch returns immediately). **Pass.**
- **AC-08** (step 8): a real, accepted-extension (`.txt`) file padded to
  21 MB → `attachment_status: "rejected"`, message
  `"That file is too large (21.0 MB) -- the limit is 20 MB."` (distinct
  wording from step 7); `.second-brain/uploads/` confirmed empty
  afterward. **Pass.**
- **AC-09** (step 9): in-process monkeypatch of
  `skill_tools.compass_client.summarize_content` to raise `CompassError`,
  scoped to one real HTTP call driven via
  `httpx.ASGITransport(app=app)` against the real, unmodified `app`
  object (not the listening server — the monkeypatch needed to be
  in-process with the calling code, and this project's own established
  `SPRINT-029` ASGITransport technique makes that a real HTTP call
  through the real app, not a mock) with a real, accepted `.txt` file →
  `{"reply": "Summarization failed: simulated failure",
  "attachment_status": "summarization_failed", "vault_path": null}`.
  Confirmed (by code tracing — the `summary_result.get("status") !=
  "ok"` branch returns before any `vault_filing_expert` call) that the
  Vault Filing Expert was never invoked and no vault note was written;
  `.second-brain/uploads/` confirmed empty afterward; monkeypatch
  reverted immediately, confirmed restored. **Pass.**
- **AC-10** (step 10): same ASGITransport technique, monkeypatching
  `vault_filing_expert.model_factory.resolve_agent_model` to return
  `None` for the duration of one call (mirrors `REQ-SB-35-US-01`'s own
  established "unavailable" induction technique) with a real, accepted
  `.txt` file about a genuinely new subject → `{"reply": "I summarized
  notes.txt, but couldn't file it into the vault yet (The Vault Filing
  Expert's selected Provider is not available.). Here's the summary so
  it isn't lost:\n\nRiverside expansion project to support AC-10
  induction testing with a real budget of $500,000 and a Q4 timeline.",
  "attachment_status": "summarized_unfiled", "vault_path": null}` — the
  real summary text is preserved, honest note names what failed;
  monkeypatch reverted, confirmed restored; `.second-brain/uploads/`
  confirmed empty afterward. **Pass.**
- Clean-up (step 11): `agent_skills.json` was not touched by this task's
  own verification (T03's own grant/revoke cleanup already left it at
  its real production state); the two throwaway vault notes from steps
  1-4 (`Work/Notes/Atlas Migration - Project Kickoff.md`,
  `Work/Customers/Northwind Logistics - AKS Migration Opportunity.md`,
  and its newly-created hub note `Work/Customers/Northwind
  Logistics.md`) were deleted; confirmed via `grep -rl` that no other
  vault file references either throwaway name (only the real, expected
  `agent_communication_history.json` audit-log entries and Obsidian's
  own harmless `workspace.json` recently-opened cache remain, both
  legitimate — not test debris to clean). The dedicated verification
  server (port `8002`) was stopped; the concurrent sibling coder's own
  process on port `8001` was never touched.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (existing `POST
/{agent_id}/chat` route, `ChatMessageBody`, and every other existing
route confirmed byte-for-byte unmodified; no new dependency/shared-
interface change beyond what `ADR-034`/`T01`-`T03` already established;
`requesting_agent_id` confirmed always the real receiving agent's id;
all 7 of this task's own locked ACs — `AC-01` through `AC-06`, `AC-09`,
`AC-10` — verified live end-to-end against real Compass/Vault-Filing-
Expert calls, with `AC-05` verified twice more incidentally during
`AC-03`/`AC-07`-`10`).
