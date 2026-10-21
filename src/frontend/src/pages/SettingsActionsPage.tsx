import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { Field } from '../features/settings/Field';
import { extractErrorDetail } from '../features/settings/artifactFlowUtils';
import {
  ACTION_IMPLEMENTATION_KINDS,
  confirmActionCall,
  createAction,
  declineActionCall,
  deleteAction,
  setActionBlocked,
  fetchAction,
  fetchActions,
  fetchPendingActionCalls,
  updateAction,
  type ActionCatalogueEntry,
  type ActionImplementationKind,
  type ActionImplementationWrite,
  type ActionInputField,
  type ActionWriteBody,
  type PendingActionCall,
} from '../features/settings/actionsApiClient';

// The Action catalogue and its one-Action editor (REQ-SB-95-US-02-T06,
// ADR-032) -- the sixth artifact kind's own Settings page, on the
// already-approved .item-list/.item-row and .input/Save changes families
// rather than any new visual system (the operator's own functional-first
// precedent, 2026-08-31).
//
// Two backend contracts this screen exists on the right side of:
//
// - **It is not the enforcement point.** Exactly-one-implementation and
//   save-time resolution are ActionManager's rules; a refused save is
//   rendered with the backend's own sentence, verbatim, because that
//   sentence names the skill / route / feature key that did not resolve.
//   The Save button is therefore never disabled for "no implementation
//   chosen" -- refusing it here would replace that sentence with a guess.
// - **Read and write shape `implementation` differently.** A read returns
//   it flat with a `kind` field; a write sends the kind as a key. The
//   editor holds the operator's choice as a kind + that kind's own fields
//   and builds the write shape at save time, so nothing ever echoes a GET
//   body back into a PUT.
// - **A delete refused because a Workflow step names this Action renders
//   the backend's own sentence, verbatim** (REQ-SB-95-US-04-T07,
//   ADR-034). That sentence is what names the referencing Workflows, and
//   the operator has to clear every one of them before the Action can
//   go -- "Something went wrong" would leave them with nothing to act on.
//   It is the same 409-and-one-sentence shape every other refusal from
//   this router uses, which is why it needs no second error path here:
//   `handleDelete` renders `extractErrorDetail(error)` as-is and does NOT
//   reload the catalogue, so the Action's row is still there afterwards --
//   nothing was deleted, and the screen must not imply otherwise.
//
// It also carries the pending-confirmations region (REQ-SB-95-US-03-T04,
// ADR-033): a small surface over the Action-call ledger, on the same
// .item-list/.item-row + .btn families as the catalogue above it. It is
// NOT the archived Pending Approvals screen and revives nothing of it --
// an Action's confirmation flag is a per-operation operator decision and
// has nothing to do with an agent's working mode. Confirming here
// performs nothing: it grants the agent's next call permission to, once.

const KIND_LABELS: Record<ActionImplementationKind, string> = {
  skill: 'Deployed Skill',
  http: 'HTTP route',
  ui: 'In-app feature',
};

interface EditorDraft {
  actionId: string;
  description: string;
  inputs: ActionInputField[];
  allowedCallers: string;
  needsConfirmation: boolean;
  /** '' = the operator has chosen no implementation yet, which is a real,
   *  saveable attempt -- the backend is what refuses it. */
  implementationKind: ActionImplementationKind | '';
  skillId: string;
  method: string;
  path: string;
  featureKey: string;
  createdAt: string;
  updatedAt: string | null;
}

function emptyDraft(): EditorDraft {
  return {
    actionId: '', description: '', inputs: [], allowedCallers: '', needsConfirmation: false,
    implementationKind: '', skillId: '', method: 'GET', path: '', featureKey: '',
    createdAt: '', updatedAt: null,
  };
}

function toWriteImplementation(draft: EditorDraft): ActionImplementationWrite | null {
  if (draft.implementationKind === 'skill') return { skill: { skill_id: draft.skillId.trim() } };
  if (draft.implementationKind === 'http') {
    return { http: { method: draft.method.trim().toUpperCase(), path: draft.path.trim() } };
  }
  if (draft.implementationKind === 'ui') return { ui: { feature_key: draft.featureKey.trim() } };
  return null;
}

function toWriteBody(draft: EditorDraft): ActionWriteBody {
  return {
    description: draft.description,
    inputs: draft.inputs.map((input) => ({ ...input, name: input.name.trim() })),
    // Comma-separated in the field, a list on the wire: these are agent ids
    // (or the single "*"), and an empty field means nobody may call it --
    // a real, saveable state, not a missing value.
    allowed_callers: draft.allowedCallers.split(',').map((caller) => caller.trim()).filter(Boolean),
    needs_confirmation: draft.needsConfirmation,
    implementation: toWriteImplementation(draft),
  };
}

function describeInputs(inputs: Record<string, unknown>): string {
  const named = Object.entries(inputs).map(([name, value]) => `${name}: ${JSON.stringify(value)}`);
  return named.length === 0 ? 'No inputs.' : named.join(' · ');
}

export function SettingsActionsPage() {
  const [catalogue, setCatalogue] = useState<ActionCatalogueEntry[] | null>(null);
  const [pendingCalls, setPendingCalls] = useState<PendingActionCall[] | null>(null);
  const [draft, setDraft] = useState<EditorDraft | null>(null);
  const [editingExisting, setEditingExisting] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [pendingError, setPendingError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deciding, setDeciding] = useState<string | null>(null);

  function reload() {
    return fetchActions().then(setCatalogue);
  }

  function reloadPendingCalls() {
    return fetchPendingActionCalls().then(setPendingCalls);
  }

  useEffect(() => {
    reload();
    reloadPendingCalls();
  }, []);

  async function decideOn(callId: string, decide: (id: string) => Promise<PendingActionCall>) {
    setPendingError(null);
    setDeciding(callId);
    try {
      await decide(callId);
      // Always re-read rather than patching the row locally: whether a
      // decided call is still outstanding is the backend's rule (a
      // confirmed one stays until the agent spends it), and a screen
      // that guessed would start telling the operator a different story
      // than the ledger.
      await reloadPendingCalls();
    } catch (error) {
      setPendingError(extractErrorDetail(error));
    } finally {
      setDeciding(null);
    }
  }

  function patchDraft(patch: Partial<EditorDraft>) {
    setDraft((previous) => (previous === null ? previous : { ...previous, ...patch }));
  }

  function openNewEditor() {
    setSaveError(null);
    setEditingExisting(false);
    setDraft(emptyDraft());
  }

  async function openExistingEditor(actionId: string) {
    setSaveError(null);
    const action = await fetchAction(actionId);
    const implementation = action.implementation;
    setEditingExisting(true);
    setDraft({
      actionId: action.id,
      description: action.description,
      inputs: action.inputs.map((input) => ({ ...input })),
      allowedCallers: action.allowed_callers.join(', '),
      needsConfirmation: action.needs_confirmation,
      implementationKind: implementation?.kind ?? '',
      skillId: implementation?.skill_id ?? '',
      method: implementation?.method || 'GET',
      path: implementation?.path ?? '',
      featureKey: implementation?.feature_key ?? '',
      createdAt: action.created_at,
      updatedAt: action.updated_at,
    });
  }

  async function handleSave() {
    if (draft === null) return;
    setSaving(true);
    setSaveError(null);
    try {
      const body = toWriteBody(draft);
      if (editingExisting) {
        await updateAction(draft.actionId, body);
      } else {
        await createAction(draft.actionId.trim(), body);
      }
      await reload();
      setDraft(null);
    } catch (error) {
      // The catalogue is deliberately NOT reloaded on a refusal: nothing
      // was written, the editor keeps what the operator typed, and the
      // backend's own sentence is what they read.
      setSaveError(extractErrorDetail(error));
    } finally {
      setSaving(false);
    }
  }

  /** Throw or release the kill switch (`REQ-SB-102`).
   *
   * Blocking asks for a reason and unblocking does not: the reason is
   * what the agent is told when it tries and cannot, so an empty one
   * leaves it saying only that someone stopped it. Cancelling the
   * prompt cancels the block -- a blank reason by accident is the one
   * outcome worth refusing, since this is the message that reaches a
   * confused agent.
   */
  /** Matches handleDelete's handling: the backend's own sentence on
   * failure, and a re-read rather than a local patch, so the badge and
   * the reason come from the store instead of from a guess. */
  async function apply(work: () => Promise<unknown>) {
    setListError(null);
    try {
      await work();
      await reload();
    } catch (error) {
      setListError(extractErrorDetail(error));
    }
  }

  async function handleBlock(action: ActionCatalogueEntry) {
    if (action.is_blocked) {
      await apply(() => setActionBlocked(action.id, false));
      return;
    }
    const reason = window.prompt(
      `Block "${action.id}"?

No agent will be able to call it, and every attempt is ` +
        `refused and recorded. Why are you blocking it? The agent is told this.`,
    );
    if (reason === null) return;
    await apply(() => setActionBlocked(action.id, true, reason.trim()));
  }

  async function handleDelete(actionId: string) {
    setListError(null);
    try {
      await deleteAction(actionId);
      await reload();
      setDraft((previous) => (previous?.actionId === actionId ? null : previous));
    } catch (error) {
      setListError(extractErrorDetail(error));
    }
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <div className="artifacts-action-bar" style={{ marginBottom: 'var(--space-4)' }}>
        <h1 style={{ margin: 0 }}>Actions</h1>
        <button type="button" className="btn btn-primary" data-testid="action-new" onClick={openNewEditor}>
          New action
        </button>
      </div>
      <p className="text-muted">
        Every invocable operation this app offers, in one catalogue — each with typed inputs, who may
        call it, whether it needs confirmation, and exactly one implementation. An implementation is
        checked when the Action is saved and re-checked every time this list is read, so an Action that
        has stopped resolving says so here rather than failing when something calls it.
      </p>

      {listError && (
        <p className="text-muted" data-testid="action-list-error">
          <span className="badge badge-danger">Refused</span> {listError}
        </p>
      )}

      <div className="card" data-testid="pending-confirmations">
        <h2>Pending confirmations</h2>
        <p className="text-muted">
          An Action marked “needs confirmation” performs nothing when an agent calls it — it waits
          here. Confirming does not run it either: it grants that agent permission to run it once,
          the next time it calls. Declining stops it for good, and the agent is told so.
        </p>

        {pendingError && (
          <p className="text-muted" data-testid="pending-calls-error">
            <span className="badge badge-danger">Refused</span> {pendingError}
          </p>
        )}

        {pendingCalls === null && <p className="text-muted">Loading...</p>}
        {pendingCalls !== null && (
          <div className="item-list">
            {pendingCalls.map((pendingCall) => (
              <div
                className="item-row"
                key={pendingCall.call_id}
                data-testid={`pending-call-row-${pendingCall.call_id}`}
              >
                <div className="item-row-main">
                  <span className="item-row-title">{pendingCall.action_id}</span>
                  <span className="item-row-meta" data-testid={`pending-call-caller-${pendingCall.call_id}`}>
                    Called by {pendingCall.caller_agent_id} · {describeInputs(pendingCall.inputs)}
                  </span>
                  <span className="item-row-meta">
                    <span
                      className={`badge ${pendingCall.outcome === 'confirmed' ? 'badge-success' : ''}`}
                      data-testid={`pending-call-state-${pendingCall.call_id}`}
                    >
                      {pendingCall.outcome === 'confirmed'
                        ? 'Confirmed — not run yet'
                        : 'Awaiting your decision'}
                    </span>{' '}
                    <span className="badge">{pendingCall.recorded_at}</span>
                  </span>
                  <span className="item-row-meta" data-testid={`pending-call-detail-${pendingCall.call_id}`}>
                    {pendingCall.detail ?? pendingCall.refusal ?? pendingCall.call_id}
                  </span>
                </div>
                {/* A confirmed call has nothing left for the operator to
                    decide — the agent has to come back and spend it — so
                    it is shown without controls rather than with ones
                    that would do nothing. */}
                {pendingCall.outcome === 'awaiting_confirmation' && (
                  <div className="item-row-actions">
                    <button
                      type="button"
                      className="btn btn-primary"
                      data-testid={`pending-call-confirm-${pendingCall.call_id}`}
                      disabled={deciding === pendingCall.call_id}
                      onClick={() => decideOn(pendingCall.call_id, confirmActionCall)}
                    >
                      Confirm
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger"
                      data-testid={`pending-call-decline-${pendingCall.call_id}`}
                      disabled={deciding === pendingCall.call_id}
                      onClick={() => decideOn(pendingCall.call_id, declineActionCall)}
                    >
                      Decline
                    </button>
                  </div>
                )}
              </div>
            ))}
            {pendingCalls.length === 0 && (
              <p className="text-muted" data-testid="pending-calls-empty">
                Nothing is waiting on you.
              </p>
            )}
          </div>
        )}
      </div>

      <div className="card" style={{ marginTop: 'var(--space-4)' }}>
        <h2>Catalogue</h2>
        {catalogue === null && <p className="text-muted">Loading...</p>}
        {catalogue !== null && (
          <div className="item-list">
            {catalogue.map((action) => (
              <div className="item-row" key={action.id} data-testid={`action-row-${action.id}`}>
                <div className="item-row-main">
                  <span className="item-row-title">
                    {action.id}
                    {action.is_blocked && (
                      <>
                        {' '}
                        <span className="badge badge-danger" data-testid={`action-blocked-${action.id}`}>
                          Blocked
                        </span>
                      </>
                    )}
                  </span>
                  {action.is_blocked && (
                    <span className="item-row-meta" data-testid={`action-blocked-reason-${action.id}`}>
                      {action.blocked_reason
                        ? `Blocked: ${action.blocked_reason}`
                        : 'Blocked, with no reason recorded.'}
                    </span>
                  )}
                  <span className="item-row-meta" data-testid={`action-description-${action.id}`}>
                    {action.description || 'No description.'}
                  </span>
                  <span className="item-row-meta">
                    <span className="badge" data-testid={`action-kind-${action.id}`}>
                      {action.implementation_kind
                        ? KIND_LABELS[action.implementation_kind]
                        : 'No implementation'}
                    </span>
                    {action.plugin_id && (
                      <>
                        {' '}
                        <span className="badge" data-testid={`action-plugin-${action.id}`}>
                          From the {action.plugin_id} plugin
                        </span>
                      </>
                    )}
                    {action.status === 'broken' && (
                      <>
                        {' '}
                        <span className="badge badge-danger" data-testid={`action-broken-${action.id}`}>
                          Broken
                        </span>
                      </>
                    )}
                  </span>
                  {action.status === 'broken' && (
                    <span className="item-row-meta" data-testid={`action-broken-reason-${action.id}`}>
                      {action.reason}
                    </span>
                  )}
                  {action.plugin_id && (
                    <span className="item-row-meta">
                      Contributed while that plugin is loaded, and stored nowhere on this install — edit
                      it in the plugin, not here.
                    </span>
                  )}
                </div>
                {/* A plugin's Action has no file to change, and the backend
                    refuses both writes on it, so no edit/delete control is
                    rendered for one at all. */}
                {!action.plugin_id && (
                  <div className="item-row-actions">
                    <button
                      type="button"
                      className="btn"
                      data-testid={`action-edit-${action.id}`}
                      onClick={() => openExistingEditor(action.id)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn"
                      data-testid={`action-block-${action.id}`}
                      onClick={() => handleBlock(action)}
                    >
                      {action.is_blocked ? 'Unblock' : 'Block'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-danger"
                      data-testid={`action-delete-${action.id}`}
                      onClick={() => handleDelete(action.id)}
                    >
                      Delete
                    </button>
                  </div>
                )}
              </div>
            ))}
            {catalogue.length === 0 && (
              <p className="text-muted" data-testid="action-catalogue-empty">No Actions yet.</p>
            )}
          </div>
        )}
      </div>

      {draft !== null && (
        <div className="card" style={{ marginTop: 'var(--space-4)' }} data-testid="action-editor">
          <h2>{editingExisting ? `Edit ${draft.actionId}` : 'New action'}</h2>

          {saveError && (
            <p className="text-muted" data-testid="action-editor-error">
              <span className="badge badge-danger">Save refused</span> {saveError}
            </p>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <Field label="Action id">
              {editingExisting ? (
                <span className="item-row-meta" data-testid="action-editor-id">{draft.actionId}</span>
              ) : (
                <input
                  className="input"
                  data-testid="action-editor-id"
                  placeholder="e.g. make-entity-strategic"
                  value={draft.actionId}
                  onChange={(event) => patchDraft({ actionId: event.target.value })}
                />
              )}
            </Field>

            <Field label="Description">
              <textarea
                className="input"
                rows={2}
                style={{ width: '100%', resize: 'vertical' }}
                data-testid="action-editor-description"
                value={draft.description}
                onChange={(event) => patchDraft({ description: event.target.value })}
              />
            </Field>

            <Field label="Inputs">
              <div className="item-list" data-testid="action-editor-inputs">
                {draft.inputs.map((input, index) => (
                  <div className="item-row" key={index} data-testid={`action-input-row-${index}`}>
                    <div className="item-row-main">
                      <input
                        className="input"
                        placeholder="name"
                        data-testid={`action-input-name-${index}`}
                        value={input.name}
                        onChange={(event) => patchDraft({
                          inputs: draft.inputs.map((entry, position) => (
                            position === index ? { ...entry, name: event.target.value } : entry
                          )),
                        })}
                      />
                      <input
                        className="input"
                        placeholder="type (e.g. string)"
                        data-testid={`action-input-type-${index}`}
                        value={input.type}
                        onChange={(event) => patchDraft({
                          inputs: draft.inputs.map((entry, position) => (
                            position === index ? { ...entry, type: event.target.value } : entry
                          )),
                        })}
                      />
                      <input
                        className="input"
                        placeholder="description"
                        data-testid={`action-input-description-${index}`}
                        value={input.description}
                        onChange={(event) => patchDraft({
                          inputs: draft.inputs.map((entry, position) => (
                            position === index ? { ...entry, description: event.target.value } : entry
                          )),
                        })}
                      />
                    </div>
                    <div className="item-row-actions">
                      <label className="badge" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                        <input
                          type="checkbox"
                          data-testid={`action-input-required-${index}`}
                          checked={input.required}
                          style={{ margin: 0 }}
                          onChange={(event) => patchDraft({
                            inputs: draft.inputs.map((entry, position) => (
                              position === index ? { ...entry, required: event.target.checked } : entry
                            )),
                          })}
                        />
                        Required
                      </label>
                      <button
                        type="button"
                        className="btn btn-danger"
                        data-testid={`action-input-remove-${index}`}
                        onClick={() => patchDraft({
                          inputs: draft.inputs.filter((_, position) => position !== index),
                        })}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
                {draft.inputs.length === 0 && <span className="item-row-meta">No inputs declared.</span>}
                <div>
                  <button
                    type="button"
                    className="btn"
                    data-testid="action-input-add"
                    onClick={() => patchDraft({
                      inputs: [...draft.inputs, { name: '', type: 'string', required: false, description: '' }],
                    })}
                  >
                    Add input
                  </button>
                </div>
              </div>
            </Field>

            <Field label="Allowed callers (agent ids, comma-separated, or *)">
              <input
                className="input"
                placeholder="e.g. research-hub, inbox-triage — or *"
                data-testid="action-editor-allowed-callers"
                value={draft.allowedCallers}
                onChange={(event) => patchDraft({ allowedCallers: event.target.value })}
              />
              <span className="item-row-meta">Leave empty for an Action nothing may call yet.</span>
            </Field>

            <label className="badge" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', alignSelf: 'flex-start' }}>
              <input
                type="checkbox"
                data-testid="action-editor-needs-confirmation"
                checked={draft.needsConfirmation}
                style={{ margin: 0 }}
                onChange={(event) => patchDraft({ needsConfirmation: event.target.checked })}
              />
              Needs confirmation before it runs
            </label>

            <Field label="Implementation (exactly one)">
              {/* One radio group, so the browser itself clears the previous
                  choice: the picker structurally cannot hold two at once. */}
              <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }} data-testid="action-editor-implementation">
                {ACTION_IMPLEMENTATION_KINDS.map((kind) => (
                  <label
                    key={kind}
                    className={`badge ${draft.implementationKind === kind ? 'badge-success' : ''}`}
                    style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                  >
                    <input
                      type="radio"
                      name="action-implementation-kind"
                      data-testid={`action-implementation-kind-${kind}`}
                      checked={draft.implementationKind === kind}
                      style={{ margin: 0 }}
                      onChange={() => patchDraft({ implementationKind: kind })}
                    />
                    {KIND_LABELS[kind]}
                  </label>
                ))}
              </div>
              {draft.implementationKind === '' && (
                <span className="item-row-meta">Nothing chosen yet.</span>
              )}
              {draft.implementationKind === 'skill' && (
                <input
                  className="input"
                  placeholder="deployed skill id, e.g. outlook-email-thread-capture"
                  data-testid="action-implementation-skill-id"
                  value={draft.skillId}
                  onChange={(event) => patchDraft({ skillId: event.target.value })}
                />
              )}
              {draft.implementationKind === 'http' && (
                <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
                  <input
                    className="input"
                    placeholder="GET"
                    style={{ maxWidth: '8rem' }}
                    data-testid="action-implementation-http-method"
                    value={draft.method}
                    onChange={(event) => patchDraft({ method: event.target.value })}
                  />
                  <input
                    className="input"
                    placeholder="/vault-index/refresh"
                    data-testid="action-implementation-http-path"
                    value={draft.path}
                    onChange={(event) => patchDraft({ path: event.target.value })}
                  />
                </div>
              )}
              {draft.implementationKind === 'ui' && (
                <input
                  className="input"
                  placeholder="a route this app's front end registers, e.g. /settings/artifacts"
                  data-testid="action-implementation-ui-feature-key"
                  value={draft.featureKey}
                  onChange={(event) => patchDraft({ featureKey: event.target.value })}
                />
              )}
            </Field>

            {editingExisting && (
              <span className="item-row-meta" data-testid="action-editor-timestamps">
                Created {draft.createdAt || 'unknown'}
                {draft.updatedAt ? ` · last updated ${draft.updatedAt}` : ' · never updated'}
              </span>
            )}

            <div className="item-row-actions">
              <button
                type="button"
                className="btn btn-primary"
                data-testid="action-editor-save"
                disabled={saving}
                onClick={handleSave}
              >
                Save changes
              </button>
              <button
                type="button"
                className="btn"
                data-testid="action-editor-cancel"
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
