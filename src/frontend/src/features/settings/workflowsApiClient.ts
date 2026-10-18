import { apiFetch } from '../../api/client';

// Workflow catalogue (REQ-SB-95-US-04-T07) -- a thin client over the real
// GET/POST/PUT/DELETE /workflows endpoints (app/api/workflows_router.py),
// same apiFetch helper and same shape as actionsApiClient.ts.
//
// Two backend contracts this client exists to keep visible to its screen:
//
// - **Read and write shape the SAME way**, unlike the Action surface: a
//   stored step carries exactly the five fields a written one does, so a
//   `GET` body posted straight back is a valid write. The one asymmetry
//   is that `created_at`/`updated_at` are the Manager's own facts and are
//   refused on a write, and `id` is settable only at creation.
// - **A supplied `steps` REPLACES the stored list, in the order given** --
//   that IS what a reorder is, and there is no merge by step id. So every
//   save sends every step the operator still wants, carrying the id each
//   already has: dropping an id would re-key that step and a run started
//   against the old definition would record its outcome against whatever
//   had moved into that position (`ADR-034`).

/** One documented step. `id` is the step's stable handle and is `''` only
 *  for a step the operator has just added -- the Manager mints one at
 *  save time. `inputs` is an open dict this screen stores and interprets
 *  for nobody: the call gate validates it against the Action's declared
 *  inputs when the step is dispatched (`ADR-033`). */
export interface WorkflowStep {
  id: string;
  action_id: string;
  inputs: Record<string, unknown>;
  needs_confirmation: boolean;
  description: string;
}

/** An empty `include_step_ids` means every step, in documented order --
 *  the entity's own default, not a missing value. */
export interface WorkflowReport {
  description: string;
  include_step_ids: string[];
}

export interface Workflow {
  id: string;
  request_kind: string;
  description: string;
  steps: WorkflowStep[];
  report: WorkflowReport;
  created_at: string;
  updated_at: string | null;
}

/** `id`, `created_at` and `updated_at` are the backend's and are absent
 *  here by type; everything else round-trips unchanged. */
export interface WorkflowWriteBody {
  request_kind: string;
  description: string;
  steps: WorkflowStep[];
  report: WorkflowReport;
}

export function fetchWorkflows(): Promise<Workflow[]> {
  return apiFetch('/workflows');
}

export function fetchWorkflow(workflowId: string): Promise<Workflow> {
  return apiFetch(`/workflows/${encodeURIComponent(workflowId)}`);
}

/** POST onto an id this install already has **replaces** that Workflow --
 *  the same thing POST /actions does, and the reason the screen tells the
 *  operator so before they save rather than reporting a replacement as a
 *  creation. */
export function createWorkflow(workflowId: string, body: WorkflowWriteBody): Promise<Workflow> {
  return apiFetch('/workflows', {
    method: 'POST',
    body: JSON.stringify({ id: workflowId, ...body }),
  });
}

export function updateWorkflow(workflowId: string, body: WorkflowWriteBody): Promise<Workflow> {
  return apiFetch(`/workflows/${encodeURIComponent(workflowId)}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export function deleteWorkflow(workflowId: string): Promise<{ deleted: boolean }> {
  return apiFetch(`/workflows/${encodeURIComponent(workflowId)}`, { method: 'DELETE' });
}
