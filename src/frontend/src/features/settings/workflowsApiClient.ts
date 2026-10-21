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

/** What a step is. A Workflow is not a fixed script of Action calls
 *  (`REQ-SB-103`): a step may be an Action the app performs, another
 *  agent the run is handed to, or a question for a person. */
export type WorkflowStepKind = 'action' | 'agent' | 'human';

/** One documented step. `id` is the step's stable handle and is `''` only
 *  for a step the operator has just added -- the Manager mints one at
 *  save time. `inputs` is an open dict this screen stores and interprets
 *  for nobody: the call gate validates it against the Action's declared
 *  inputs when the step is dispatched (`ADR-033`).
 *
 *  Which fields a step needs follows from its `kind`, and that rule is
 *  the Manager's -- an action step names an Action, an agent step names
 *  an agent and what to ask it, a human step names what to ask the
 *  person. The unused fields are still sent, empty, because a save
 *  replaces the stored list wholesale and a field dropped here is
 *  dropped on disk.
 *
 *  An input or an `ask` may hold a reference instead of a literal:
 *  `{{request.customer}}` for what the ask was about, or
 *  `{{steps.<step_id>.result}}` for what an earlier step came back
 *  with. They are resolved when the step is reached, and an
 *  unresolvable one refuses the step rather than being passed through. */
export interface WorkflowStep {
  id: string;
  kind: WorkflowStepKind;
  action_id: string;
  agent_id: string;
  ask: string;
  /** Human steps only: whether the person may change what was proposed
   *  before it goes on, rather than only approving or declining it. */
  allows_edit: boolean;
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

// Runs held at a question (`REQ-SB-103`). A human step can hold a run
// indefinitely, so "what is waiting on me" is a real surface and not a
// convenience: a run that waits forever with nothing showing it is
// waiting is worse than one that fails.

/** One pending question. `for_person` is whose door the ask came in
 *  through, resolved when the run started; `is_for_anybody` is a run
 *  through a door nobody owns, which appears on EVERY person's list --
 *  leaving it off each one is exactly how it would be waited on by no
 *  one. `asks` is the resolved question, never the reference that named
 *  it. `unreadable` is set instead of the rest when the run's record
 *  could not be read: a pending question is reported as unreadable
 *  rather than dropped. */
export interface WaitingQuestion {
  run_id: string;
  workflow_id?: string;
  request_kind?: string;
  caller_agent_id?: string;
  entry_point?: { source?: string; chat_id?: string } | null;
  for_person?: { user_id: string; username: string; display_name: string } | null;
  is_for_anybody?: boolean;
  step_id?: string;
  position?: number;
  description?: string;
  asks?: unknown;
  allows_edit?: boolean;
  asked_at?: string | null;
  started_at?: string | null;
  unreadable?: string;
}

/** `scope: 'all'` is every pending question on the install; the default
 *  is the signed-in person's, plus every unowned one. */
export function fetchQuestionsWaitingOnAPerson(scope: 'mine' | 'all' = 'mine'): Promise<WaitingQuestion[]> {
  return apiFetch(`/workflows/runs/waiting-on-a-person?scope=${scope}`);
}

export type HumanDecision = 'approved' | 'edited' | 'declined';

/** Who answered is taken from the signed-in session and is never sent:
 *  a route that accepted a name would let any caller write "the Admin
 *  approved this" into a record whose whole value is that it cannot be.
 *  `result` is what goes on to the steps that reference this one, and an
 *  edit must supply it. */
export function answerHumanStep(
  runId: string,
  stepId: string,
  body: { decision: HumanDecision; said: string; result?: unknown },
): Promise<unknown> {
  return apiFetch(
    `/workflows/runs/${encodeURIComponent(runId)}/steps/${encodeURIComponent(stepId)}/answer`,
    { method: 'POST', body: JSON.stringify(body) },
  );
}
