---
id: REQ-SB-44-US-01-T05
title: Extend src/frontend/src/features/cockpit/cockpitApiClient.ts — fetchAttachments/handOffAttachment
parent_story: REQ-SB-44-US-01
requirement_id: REQ-SB-44
type: frontend
status: Done
gate: clear
gate_reason: ""
phase: P1
depends_on: [REQ-SB-44-US-01-T04, REQ-SB-43-US-01-T07]
created: 2026-08-14
updated: 2026-08-14
---

# REQ-SB-44-US-01-T05 — Frontend attachment client functions

## Parent Story

- Story: [[REQ-SB-44-US-01]] — `../UserStories/REQ-SB-44-US-01-inbox-cockpit-expert-assisted-workspace.md`
- Requirement: `Documentation/PRD.md` → REQ-SB-44 *Inbox Cockpit — Expert-Assisted Email Workspace*

---

## Objective

Add two functions to `REQ-SB-43-US-01-T07`'s own `cockpitApiClient.ts` file — the same shared client both stories use — over `T04`'s two new attachment routes.

---

## Starting State → End State

**Before / Inputs:** `REQ-SB-43-US-01-T07` has landed `cockpitApiClient.ts`'s six existing functions.

**After / Outputs:** two new exports appended to the SAME file:
```typescript
export interface CockpitAttachment {
  filename: string;
  size: number;
}

export function fetchCockpitAttachments(stem: string): Promise<CockpitAttachment[]> {
  return apiFetch<CockpitAttachment[]>(`/cockpit/email/${stem}/attachments`);
}

export function handOffAttachment(stem: string, filename: string): Promise<{ status: string; summary?: string }> {
  return apiFetch<{ status: string; summary?: string }>(`/cockpit/email/${stem}/attachments/${filename}/hand-off`, {
    method: 'POST',
  });
}
```

---

## Files to Modify

- `src/frontend/src/features/cockpit/cockpitApiClient.ts` — add the two functions above, additive. Do not modify the six existing exports.

---

## Constraints

- Uses `apiFetch`, matching the file's own existing convention.
- Does not modify any of `REQ-SB-43-US-01-T07`'s own six existing exports.

---

## Tests

**Manual verification steps** (real backend dev server; requires a real Email note with an attachment, per `T04`'s own Tests):
1. **[REQ-SB-44-US-01-AC-04]** `fetchCockpitAttachments("<real-stem>")` — confirm a real list matching `T04`'s own real response.
2. **[REQ-SB-44-US-01-AC-05]** `fetchCockpitAttachments("<stem-with-no-attachments>")` → `[]`.
3. **[REQ-SB-44-US-01-AC-04]** `handOffAttachment("<real-stem>", "<real-filename>")` — confirm a real `{"status": "ok", "summary": ...}`.

**Automated tests:** `n/a — test tooling pending`

> On test failure: read the error, fix the root cause, re-run. After 3 attempts,
> stop and report the failure to the user.

---

## Acceptance Criteria

- [x] `fetchCockpitAttachments`/`handOffAttachment` exist, calling `T04`'s real routes via `apiFetch`
- [x] `REQ-SB-43-US-01-T07`'s own six existing exports unmodified
- [x] `MEMORY.md` updated if this task produced a new decision / pattern / constraint
- [x] `CHANGELOG.md` entry appended

---

## Out of Scope

- Rendering — `T06`.

---

## Context / Notes

Shared client file, per `ADR-036` point 3.

---

## Implementation Log

**2026-08-14 — built exactly per the task's own code block, no deviation.** `cockpitApiClient.ts` gained `CockpitAttachment`, `fetchCockpitAttachments`, `handOffAttachment`, appended after `saveCockpitResearch`; `REQ-SB-43-US-01-T07`'s own six existing exports read first and left unmodified.

**Verification (real backend on port 8001 + a dedicated real frontend dev server on port 5174 pointed at it via `VITE_API_BASE_URL`, a real headless-Edge CDP session driving the ACTUAL served module via `await import('/src/features/cockpit/cockpitApiClient.ts')` from the browser's own JS runtime — not a mock):**

- **[AC-04]** `fetchCockpitAttachments("2026-08-12-Emailing%20Sarmad_Jari_Resume.pdf-10930000")` (real, URL-encoded stem) → `[{"filename":"Sarmad_Jari_Resume.pdf","size":342594}]`, matching `T04`'s own real response exactly. **Pass.**
- **[AC-05]** `fetchCockpitAttachments("<stem-with-no-attachments>")` → `[]`. **Pass.**
- **[AC-04]** `handOffAttachment(<real-stem>, "Sarmad_Jari_Resume.pdf")` → real `{"status":"ok","summary":<2061-char real Compass summary>}`. **Pass.**
- Clean-up: the real `.second-brain/cockpit_threads.json` test entry created by this verification pass was removed immediately after.

`gate: clear` 2026-08-14 — no MUST-FLAG trigger fired (no deviation from the task's own code sample; additive-only client change; both locked ACs this task supports verified live, in a real browser, against the real served module and real backend).
