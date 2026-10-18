import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { Field } from '../features/settings/Field';
import { extractErrorDetail } from '../features/settings/artifactFlowUtils';
import { fetchActions, type ActionCatalogueEntry } from '../features/settings/actionsApiClient';
import {
  createWorkflow,
  deleteWorkflow,
  fetchWorkflow,
  fetchWorkflows,
  updateWorkflow,
  type Workflow,
  type WorkflowStep,
} from '../features/settings/workflowsApiClient';

// The Workflow catalogue and its ordered-step editor (REQ-SB-95-US-04-T07,
// ADR-032/ADR-034) -- the seventh artifact kind's own Settings page, on the
// already-approved .item-list/.item-row and .input/Save changes families
// the Actions page (its sibling, one story older) established.
//
// What this screen is on the right side of:
//
// - **It is not the enforcement point.** That every step names a real
//   catalogued Action is WorkflowManager's rule, checked at save before
//   anything is written. A refused save is rendered with the backend's own
//   sentence, verbatim, because that sentence names WHICH step (by the
//   position this editor shows) and WHICH unknown action id -- the only
//   part the operator can act on. Save is therefore never disabled to
//   pre-empt a refusal: refusing here would replace that sentence with a
//   guess.
// - **Reordering is plain move controls, not drag-and-drop** (the
//   operator's own functional-first precedent, 2026-08-31). Position is
//   the only control flow a Workflow has, and a save sends the whole list
//   in its displayed order, each step carrying the id it already has --
//   `ADR-034` addresses a step by id, so a reorder must move ids, not
//   re-key them.
// - **Read, unread and empty are three different renderings.** A region
//   whose fetch failed says so and names what it tried to read; only a
//   region that was genuinely read and found empty gets the empty wording
//   (SPRINT-091's rule). The step picker in particular never silently
//   becomes an empty `<select>` because `GET /actions` failed.
// - **A step whose Action is no longer catalogued keeps its id, shown as
//   such.** A `<select>` with no matching option would display its first
//   option instead, which would quietly rewrite the operator's stored step
//   into a different Action -- so the unknown id is carried as its own
//   option, labelled, and the backend is left to refuse the save.
//
// Runs are NOT here. Starting a run, handing back one step at a time and
// composing the report are T05/T06's, over their own store; a run surface
// that existed and did nothing would read exactly like a run engine that
// silently loses steps.

/** The one Workflow being edited. `steps` holds real `WorkflowStep`s --
 *  including `inputs`, which this editor does not change and must
 *  therefore carry through verbatim: a save replaces the stored list
 *  wholesale, so anything dropped here is dropped on disk. */
interface EditorDraft {
  workflowId: string;
  requestKind: string;
  description: string;
  steps: WorkflowStep[];
  reportDescription: string;
  reportStepIds: string[];
  createdAt: string;
  updatedAt: string | null;
}

function emptyDraft(): EditorDraft {
  return {
    workflowId: '', requestKind: '', description: '', steps: [],
    reportDescription: '', reportStepIds: [], createdAt: '', updatedAt: null,
  };
}

function toDraft(workflow: Workflow): EditorDraft {
  return {
    workflowId: workflow.id,
    requestKind: workflow.request_kind,
    description: workflow.description,
    steps: workflow.steps.map((step) => ({ ...step, inputs: { ...step.inputs } })),
    reportDescription: workflow.report.description,
    reportStepIds: [...workflow.report.include_step_ids],
    createdAt: workflow.created_at,
    updatedAt: workflow.updated_at,
  };
}

function describeInputs(inputs: Record<string, unknown>): string {
  const named = Object.entries(inputs).map(([name, value]) => `${name}: ${JSON.stringify(value)}`);
  return named.length === 0 ? 'No inputs stored.' : named.join(' · ');
}

export function SettingsWorkflowsPage() {
  const [catalogue, setCatalogue] = useState<Workflow[] | null>(null);
  const [catalogueError, setCatalogueError] = useState<string | null>(null);
  const [actions, setActions] = useState<ActionCatalogueEntry[] | null>(null);
  const [actionsError, setActionsError] = useState<string | null>(null);
  const [draft, setDraft] = useState<EditorDraft | null>(null);
  const [editingExisting, setEditingExisting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function reloadCatalogue() {
    return fetchWorkflows().then(
      (workflows) => { setCatalogue(workflows); setCatalogueError(null); },
      (error) => { setCatalogue(null); setCatalogueError(extractErrorDetail(error)); },
    );
  }

  function reloadActions() {
    return fetchActions().then(
      (catalogued) => { setActions(catalogued); setActionsError(null); },
      (error) => { setActions(null); setActionsError(extractErrorDetail(error)); },
    );
  }

  useEffect(() => {
    reloadCatalogue();
    reloadActions();
  }, []);

  function patchDraft(patch: Partial<EditorDraft>) {
    setDraft((previous) => (previous === null ? previous : { ...previous, ...patch }));
  }

  function patchStep(index: number, patch: Partial<WorkflowStep>) {
    setDraft((previous) => (previous === null ? previous : {
      ...previous,
      steps: previous.steps.map((step, position) => (position === index ? { ...step, ...patch } : step)),
    }));
  }

  /** Swaps two adjacent steps, ids and all -- the whole point of the move
   *  controls is that the same step moves, so a run already addressing it
   *  by id still means the same step. */
  function moveStep(index: number, offset: number) {
    setDraft((previous) => {
      if (previous === null) return previous;
      const target = index + offset;
      if (target < 0 || target >= previous.steps.length) return previous;
      const steps = [...previous.steps];
      [steps[index], steps[target]] = [steps[target], steps[index]];
      return { ...previous, steps };
    });
  }

  function openNewEditor() {
    setSaveError(null);
    setEditingExisting(false);
    setDraft(emptyDraft());
  }

  async function openExistingEditor(workflowId: string) {
    setSaveError(null);
    setListError(null);
    try {
      const workflow = await fetchWorkflow(workflowId);
      setEditingExisting(true);
      setDraft(toDraft(workflow));
    } catch (error) {
      setListError(extractErrorDetail(error));
    }
  }

  async function handleSave() {
    if (draft === null) return;
    setSaving(true);
    setSaveError(null);
    try {
      const body = {
        request_kind: draft.requestKind,
        description: draft.description,
        steps: draft.steps,
        report: {
          description: draft.reportDescription,
          // An id whose step is no longer in the list is dropped rather
          // than saved: the run engine composes the report from recorded
          // step outcomes, and a step that does not exist records none.
          include_step_ids: draft.reportStepIds.filter(
            (stepId) => draft.steps.some((step) => step.id === stepId),
          ),
        },
      };
      if (editingExisting) {
        await updateWorkflow(draft.workflowId, body);
      } else {
        await createWorkflow(draft.workflowId.trim(), body);
      }
      await reloadCatalogue();
      setDraft(null);
    } catch (error) {
      // The Workflow catalogue is deliberately NOT reloaded on a refusal:
      // nothing was written, the editor keeps what the operator authored,
      // and the backend's own sentence -- naming the step and the unknown
      // action id -- is what they read.
      //
      // The ACTION catalogue is re-read, though. A refusal is proof that
      // the list this picker was built from is out of date (an Action was
      // deleted elsewhere), and leaving the stale option unlabelled would
      // have the screen still presenting a dead action id as a catalogued
      // one, directly under a message saying it is not.
      setSaveError(extractErrorDetail(error));
      await reloadActions();
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(workflowId: string) {
    setListError(null);
    try {
      await deleteWorkflow(workflowId);
      await reloadCatalogue();
      setDraft((previous) => (previous?.workflowId === workflowId ? null : previous));
    } catch (error) {
      setListError(extractErrorDetail(error));
    }
  }

  const catalogueActionIds = (actions ?? []).map((action) => action.id);
  // A save onto an id this install already has REPLACES that Workflow
  // (POST /workflows, same as POST /actions). The operator is told before
  // they save, because "New workflow" would otherwise be the screen's own
  // word for overwriting something.
  const replacesExisting = draft !== null
    && !editingExisting
    && (catalogue ?? []).some((workflow) => workflow.id === draft.workflowId.trim());

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <div className="artifacts-action-bar" style={{ marginBottom: 'var(--space-4)' }}>
        <h1 style={{ margin: 0 }}>Workflows</h1>
        <button type="button" className="btn btn-primary" data-testid="workflow-new" onClick={openNewEditor}>
          New workflow
        </button>
      </div>
      <p className="text-muted">
        How a particular kind of request is handled: the ordered steps you decided on, which of them
        need your confirmation, and what gets reported back. Each step runs one catalogued Action, so a
        Workflow can only ask for things this app can actually do — and an Action a step names cannot be
        deleted while the step still names it.
      </p>

      {listError && (
        <p className="text-muted" data-testid="workflow-list-error">
          <span className="badge badge-danger">Refused</span> {listError}
        </p>
      )}

      <div className="card">
        <h2>Catalogue</h2>
        {catalogueError !== null && (
          <p className="text-muted" data-testid="workflow-catalogue-error">
            <span className="badge badge-danger">Could not be read</span>{' '}
            This install's Workflows could not be read from <code>GET /workflows</code>: {catalogueError}
          </p>
        )}
        {catalogue === null && catalogueError === null && <p className="text-muted">Loading...</p>}
        {catalogue !== null && (
          <div className="item-list">
            {catalogue.map((workflow) => (
              <div className="item-row" key={workflow.id} data-testid={`workflow-row-${workflow.id}`}>
                <div className="item-row-main">
                  <span className="item-row-title">{workflow.id}</span>
                  <span className="item-row-meta" data-testid={`workflow-request-kind-${workflow.id}`}>
                    Handles: {workflow.request_kind || 'no request kind documented yet'}
                  </span>
                  <span className="item-row-meta" data-testid={`workflow-description-${workflow.id}`}>
                    {workflow.description || 'No description.'}
                  </span>
                  <span className="item-row-meta">
                    <span className="badge" data-testid={`workflow-step-count-${workflow.id}`}>
                      {workflow.steps.length === 1 ? '1 step' : `${workflow.steps.length} steps`}
                    </span>{' '}
                    <span className="badge" data-testid={`workflow-step-order-${workflow.id}`}>
                      {workflow.steps.length === 0
                        ? 'No steps yet'
                        : workflow.steps.map((step) => step.action_id || '(no action)').join(' → ')}
                    </span>
                  </span>
                </div>
                <div className="item-row-actions">
                  <button
                    type="button"
                    className="btn"
                    data-testid={`workflow-edit-${workflow.id}`}
                    onClick={() => openExistingEditor(workflow.id)}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    className="btn btn-danger"
                    data-testid={`workflow-delete-${workflow.id}`}
                    onClick={() => handleDelete(workflow.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
            {catalogue.length === 0 && (
              <p className="text-muted" data-testid="workflow-catalogue-empty">No Workflows yet.</p>
            )}
          </div>
        )}
      </div>

      {draft !== null && (
        <div className="card" style={{ marginTop: 'var(--space-4)' }} data-testid="workflow-editor">
          <h2>{editingExisting ? `Edit ${draft.workflowId}` : 'New workflow'}</h2>

          {saveError && (
            <p className="text-muted" data-testid="workflow-editor-error">
              <span className="badge badge-danger">Save refused</span> {saveError}
            </p>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <Field label="Workflow id">
              {editingExisting ? (
                <span className="item-row-meta" data-testid="workflow-editor-id">{draft.workflowId}</span>
              ) : (
                <input
                  className="input"
                  data-testid="workflow-editor-id"
                  placeholder="e.g. assigned-actions-to-my-team-by-mail"
                  value={draft.workflowId}
                  onChange={(event) => patchDraft({ workflowId: event.target.value })}
                />
              )}
              {replacesExisting && (
                <span className="item-row-meta" data-testid="workflow-editor-replaces">
                  <span className="badge badge-danger">Replaces</span>{' '}
                  This install already has a Workflow with this id. Saving replaces it — this is not a
                  second Workflow.
                </span>
              )}
            </Field>

            <Field label="Kind of request this handles">
              <input
                className="input"
                data-testid="workflow-editor-request-kind"
                placeholder="e.g. send my team's assigned actions by mail"
                value={draft.requestKind}
                onChange={(event) => patchDraft({ requestKind: event.target.value })}
              />
            </Field>

            <Field label="Description">
              <textarea
                className="input"
                rows={2}
                style={{ width: '100%', resize: 'vertical' }}
                data-testid="workflow-editor-description"
                value={draft.description}
                onChange={(event) => patchDraft({ description: event.target.value })}
              />
            </Field>

            <Field label="Steps, in the order they run">
              {actionsError !== null && (
                <span className="item-row-meta" data-testid="workflow-actions-error">
                  <span className="badge badge-danger">Could not be read</span>{' '}
                  The Action catalogue could not be read from <code>GET /actions</code>, so no step
                  picker is offered: {actionsError}
                </span>
              )}
              {actions === null && actionsError === null && (
                <span className="item-row-meta">Loading the Action catalogue...</span>
              )}
              {actions !== null && actions.length === 0 && (
                <span className="item-row-meta" data-testid="workflow-actions-empty">
                  This install has no catalogued Actions yet, and every step runs one — catalogue an
                  Action first.
                </span>
              )}

              <div className="item-list" data-testid="workflow-editor-steps">
                {draft.steps.map((step, index) => {
                  const picksAnUncataloguedAction = actions !== null
                    && step.action_id !== ''
                    && !catalogueActionIds.includes(step.action_id);
                  return (
                    <div className="item-row" key={step.id || `new-${index}`} data-testid={`workflow-step-row-${index}`}>
                      <div className="item-row-main">
                        <span className="item-row-title">Step {index + 1}</span>
                        {actions !== null && (
                          <select
                            className="input"
                            data-testid={`workflow-step-action-${index}`}
                            value={step.action_id}
                            onChange={(event) => patchStep(index, { action_id: event.target.value })}
                          >
                            {/* Exactly the real catalogued Actions -- plus,
                                only when this step already names something
                                the catalogue does not have, that id itself,
                                so the stored step is not silently rewritten
                                into whichever Action happened to be first. */}
                            {catalogueActionIds.map((actionId) => (
                              <option key={actionId} value={actionId}>{actionId}</option>
                            ))}
                            {picksAnUncataloguedAction && (
                              <option value={step.action_id}>
                                {step.action_id} — not in this install's Action catalogue
                              </option>
                            )}
                          </select>
                        )}
                        {actions === null && (
                          <span className="item-row-meta" data-testid={`workflow-step-action-unpickable-${index}`}>
                            Runs {step.action_id || '(no action named)'} — kept exactly as stored.
                          </span>
                        )}
                        <input
                          className="input"
                          placeholder="what this step is for"
                          data-testid={`workflow-step-description-${index}`}
                          value={step.description}
                          onChange={(event) => patchStep(index, { description: event.target.value })}
                        />
                        <span className="item-row-meta" data-testid={`workflow-step-id-${index}`}>
                          {step.id || 'This step gets its id when you save.'}
                        </span>
                        {/* Stored and interpreted by nobody here: the call
                            gate validates inputs against the Action's own
                            declared inputs when the step is dispatched.
                            Shown read-only so a save cannot quietly drop
                            what is on disk. */}
                        <span className="item-row-meta" data-testid={`workflow-step-inputs-${index}`}>
                          {describeInputs(step.inputs)}
                        </span>
                      </div>
                      <div className="item-row-actions">
                        <label className="badge" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <input
                            type="checkbox"
                            data-testid={`workflow-step-confirm-${index}`}
                            checked={step.needs_confirmation}
                            style={{ margin: 0 }}
                            onChange={(event) => patchStep(index, { needs_confirmation: event.target.checked })}
                          />
                          Needs confirmation
                        </label>
                        <button
                          type="button"
                          className="btn"
                          data-testid={`workflow-step-up-${index}`}
                          disabled={index === 0}
                          onClick={() => moveStep(index, -1)}
                        >
                          Move up
                        </button>
                        <button
                          type="button"
                          className="btn"
                          data-testid={`workflow-step-down-${index}`}
                          disabled={index === draft.steps.length - 1}
                          onClick={() => moveStep(index, 1)}
                        >
                          Move down
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger"
                          data-testid={`workflow-step-remove-${index}`}
                          onClick={() => patchDraft({
                            steps: draft.steps.filter((_, position) => position !== index),
                          })}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  );
                })}
                {draft.steps.length === 0 && (
                  <span className="item-row-meta" data-testid="workflow-editor-no-steps">No steps yet.</span>
                )}
                <div>
                  <button
                    type="button"
                    className="btn"
                    data-testid="workflow-step-add"
                    disabled={actions === null || actions.length === 0}
                    onClick={() => patchDraft({
                      steps: [...draft.steps, {
                        id: '',
                        action_id: catalogueActionIds[0] ?? '',
                        inputs: {},
                        needs_confirmation: false,
                        description: '',
                      }],
                    })}
                  >
                    Add step
                  </button>
                </div>
              </div>
            </Field>

            <Field label="What is reported back">
              <textarea
                className="input"
                rows={2}
                style={{ width: '100%', resize: 'vertical' }}
                data-testid="workflow-report-description"
                placeholder="e.g. the list that was sent, and who it went to"
                value={draft.reportDescription}
                onChange={(event) => patchDraft({ reportDescription: event.target.value })}
              />
              <span className="item-row-meta" data-testid="workflow-report-scope">
                {draft.reportStepIds.length === 0
                  ? 'Reports on every step, in order — the default while nothing is picked below.'
                  : `Reports on ${draft.reportStepIds.length} picked step(s) only.`}
              </span>
              <div className="item-list" data-testid="workflow-report-steps">
                {draft.steps.map((step, index) => (
                  step.id === '' ? (
                    <span className="item-row-meta" key={`unsaved-${index}`} data-testid={`workflow-report-step-unsaved-${index}`}>
                      Step {index + 1} has no id until you save, so it cannot be picked individually yet.
                    </span>
                  ) : (
                    <label
                      className="badge"
                      key={step.id}
                      style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    >
                      <input
                        type="checkbox"
                        data-testid={`workflow-report-step-${index}`}
                        checked={draft.reportStepIds.includes(step.id)}
                        style={{ margin: 0 }}
                        onChange={(event) => patchDraft({
                          reportStepIds: event.target.checked
                            ? [...draft.reportStepIds, step.id]
                            : draft.reportStepIds.filter((stepId) => stepId !== step.id),
                        })}
                      />
                      Step {index + 1}: {step.action_id || '(no action)'}
                    </label>
                  )
                ))}
              </div>
            </Field>

            {editingExisting && (
              <span className="item-row-meta" data-testid="workflow-editor-timestamps">
                Created {draft.createdAt || 'unknown'}
                {draft.updatedAt ? ` · last updated ${draft.updatedAt}` : ' · never updated'}
              </span>
            )}

            <div className="item-row-actions">
              <button
                type="button"
                className="btn btn-primary"
                data-testid="workflow-editor-save"
                disabled={saving}
                onClick={handleSave}
              >
                {replacesExisting ? `Replace ${draft.workflowId.trim()}` : 'Save changes'}
              </button>
              <button
                type="button"
                className="btn"
                data-testid="workflow-editor-cancel"
                onClick={() => { setDraft(null); setSaveError(null); }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
