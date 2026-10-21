import { useState } from 'react';
import { Field } from './Field';
import type { ActionCatalogueEntry, ActionInputField } from './actionsApiClient';
import type { AgentSummary } from '../agents-map/agentsApiClient';
import type { WorkflowStep, WorkflowStepKind } from './workflowsApiClient';
import { referencePathIn, referenceText, whatThisStepCanUse } from './workflowReferences';

/** One step's own fields, beside the canvas (`REQ-SB-103`).
 *
 * **The canvas shows the shape; this shows the detail.** Putting every
 * field on every card made the chain unreadable, which is the thing the
 * operator asked for — so the cards carry what you scan for and the
 * inspector carries what you type.
 *
 * **Which fields exist follows from the kind, and the Manager decides
 * that, not this panel.** An agent step names an agent and what to ask
 * it; a human step names the question; an action step names an Action.
 * A save whose kind and fields disagree is refused by the backend,
 * naming the step — this only avoids offering a field that would be
 * ignored.
 *
 * **An input can be wired to an earlier step without typing a
 * reference.** That is the point of the whole screen: `{{steps.find
 * .result}}` is exact, unmemorable, and the thing a visual builder
 * should be doing for you. The picker offers only EARLIER steps, so it
 * cannot create a reference to something that has not run; reordering
 * still can, and the canvas is what reports that.
 */
export function WorkflowStepInspector({
  step,
  steps,
  actions,
  actionsError,
  agents,
  agentsError,
  declaredInputs,
  onPatch,
}: {
  step: WorkflowStep;
  steps: WorkflowStep[];
  actions: ActionCatalogueEntry[] | null;
  actionsError: string | null;
  agents: AgentSummary[] | null;
  agentsError: string | null;
  /** What the selected Action declares it takes, fetched lazily by the
   *  page -- `GET /actions` lists Actions without their inputs, so this
   *  is a second read and is only worth making for the one step being
   *  looked at. `undefined` means not read, and the editor then offers
   *  no declared names rather than claiming the Action declares none. */
  declaredInputs: ActionInputField[] | undefined;
  onPatch: (patch: Partial<WorkflowStep>) => void;
}) {
  const kind = (step.kind ?? 'action') as WorkflowStepKind;
  const usable = whatThisStepCanUse(step, steps);
  const catalogueActionIds = (actions ?? []).map((action) => action.id);
  const agentIds = [...new Set((agents ?? []).map((agent) => agent.id))];
  const picksAnUncataloguedAction = actions !== null
    && step.action_id !== ''
    && !catalogueActionIds.includes(step.action_id);

  return (
    <div className="wf-inspector" data-testid="workflow-inspector">
      <Field label="What this step is">
        <select
          className="input"
          data-testid="workflow-inspector-kind"
          value={kind}
          onChange={(event) => onPatch({ kind: event.target.value as WorkflowStepKind })}
        >
          <option value="action">Run an Action</option>
          <option value="agent">Hand it to another agent</option>
          <option value="human">Ask a person</option>
        </select>
      </Field>

      {kind === 'action' && (
        <Field label="Which Action">
          {actionsError !== null ? (
            <span className="item-row-meta">
              <span className="badge badge-danger">Could not be read</span>{' '}
              The Action catalogue could not be read, so this step keeps what it already
              names: <code>{step.action_id || 'nothing'}</code>. {actionsError}
            </span>
          ) : actions === null ? (
            <span className="item-row-meta">Loading the Action catalogue…</span>
          ) : (
            <select
              className="input"
              data-testid="workflow-inspector-action"
              value={step.action_id}
              onChange={(event) => onPatch({ action_id: event.target.value })}
            >
              <option value="">(no action named)</option>
              {catalogueActionIds.map((actionId) => (
                <option key={actionId} value={actionId}>{actionId}</option>
              ))}
              {/* The stored id itself, when the catalogue no longer has
                  it: a select with no matching option displays its first
                  one instead, which would silently rewrite the step. */}
              {picksAnUncataloguedAction && (
                <option value={step.action_id}>
                  {step.action_id} — not in this install's Action catalogue
                </option>
              )}
            </select>
          )}
        </Field>
      )}

      {kind === 'agent' && (
        <Field label="Which agent">
          {agents !== null && agents.length > 0 ? (
            <select
              className="input"
              data-testid="workflow-inspector-agent"
              value={step.agent_id}
              onChange={(event) => onPatch({ agent_id: event.target.value })}
            >
              <option value="">(no agent named)</option>
              {agentIds.map((agentId) => (
                <option key={agentId} value={agentId}>{agentId}</option>
              ))}
              {step.agent_id !== '' && !agentIds.includes(step.agent_id) && (
                <option value={step.agent_id}>
                  {step.agent_id} — not an agent on this install
                </option>
              )}
            </select>
          ) : (
            <>
              <input
                className="input"
                data-testid="workflow-inspector-agent"
                placeholder="agent id"
                value={step.agent_id}
                onChange={(event) => onPatch({ agent_id: event.target.value })}
              />
              <span className="item-row-meta">
                {agentsError !== null
                  ? `The agent roster could not be read, so type the id: ${agentsError}`
                  : 'No agent roster to pick from, so type the id.'}
              </span>
            </>
          )}
        </Field>
      )}

      {(kind === 'agent' || kind === 'human') && (
        <Field label={kind === 'agent' ? 'What to ask that agent' : 'What to ask the person'}>
          <WiredValue
            value={step.ask}
            usable={usable}
            placeholder={kind === 'agent'
              ? 'what that agent should do with this'
              : 'the question they answer — "shall I send this?"'}
            testId="workflow-inspector-ask"
            onChange={(next) => onPatch({ ask: next })}
          />
          {kind === 'human' && (
            <label className="badge" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', marginTop: '8px' }}>
              <input
                type="checkbox"
                data-testid="workflow-inspector-allows-edit"
                checked={step.allows_edit}
                style={{ margin: 0 }}
                onChange={(event) => onPatch({ allows_edit: event.target.checked })}
              />
              They may change it before it goes
            </label>
          )}
          {kind === 'human' && (
            <span className="item-row-meta">
              Unticked, they can only approve or decline. Ticked, what they send instead is what
              the steps after this one are given.
            </span>
          )}
        </Field>
      )}

      {kind === 'action' && (
        <Field label="What this Action is called with">
          <InputsEditor
            step={step}
            usable={usable}
            declaredInputs={declaredInputs}
            onPatch={onPatch}
          />
        </Field>
      )}

      <Field label="What this step is for">
        <input
          className="input"
          placeholder="in your own words, for whoever reads the run afterwards"
          data-testid="workflow-inspector-description"
          value={step.description}
          onChange={(event) => onPatch({ description: event.target.value })}
        />
      </Field>

      {kind === 'action' && (
        <label className="badge" style={{ cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          <input
            type="checkbox"
            data-testid="workflow-inspector-confirm"
            checked={step.needs_confirmation}
            style={{ margin: 0 }}
            onChange={(event) => onPatch({ needs_confirmation: event.target.checked })}
          />
          Ask me before this one runs
        </label>
      )}

      <p className="item-row-meta" data-testid="workflow-inspector-id">
        {step.id
          ? <>Step id <code>{step.id}</code> — a run addresses it by this, never by position, so
              moving it keeps it the same step.</>
          : 'This step gets its id when you save.'}
      </p>
    </div>
  );
}

/** A value that may be typed OR wired to something earlier in the run.
 *
 * Two controls over one field rather than a mode switch: typing is the
 * common case and must stay a plain text box, and wiring replaces the
 * whole value because that is the only shape the backend supports.
 * Picking a source overwrites what was typed, which is why the box
 * shows the reference in full afterwards instead of hiding it behind a
 * chip — the operator can see exactly what will be sent.
 */
function WiredValue({
  value,
  usable,
  placeholder,
  testId,
  onChange,
}: {
  value: string;
  usable: ReturnType<typeof whatThisStepCanUse>;
  placeholder: string;
  testId: string;
  onChange: (next: string) => void;
}) {
  const wired = referencePathIn(value);
  return (
    <div className="wf-wired">
      <input
        className={wired ? 'input wf-wired-input wf-wired-input--wired' : 'input wf-wired-input'}
        placeholder={placeholder}
        data-testid={testId}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
      <select
        className="input wf-wired-picker"
        data-testid={`${testId}-source`}
        value={wired ?? ''}
        onChange={(event) => onChange(event.target.value ? referenceText(event.target.value) : '')}
      >
        <option value="">type it instead…</option>
        {usable.steps.length > 0 && (
          <optgroup label="what an earlier step came back with">
            {usable.steps.map((candidate, index) => (
              <option key={candidate.id} value={`steps.${candidate.id}.result`}>
                step {index + 1}: {candidate.id}
              </option>
            ))}
          </optgroup>
        )}
        {usable.requestKeys.length > 0 && (
          <optgroup label="what the ask was about">
            {usable.requestKeys.map((key) => (
              <option key={key} value={`request.${key}`}>{key}</option>
            ))}
          </optgroup>
        )}
      </select>
    </div>
  );
}

/** The named values an Action step is called with.
 *
 * The Action's own declared inputs are offered as the names to add,
 * because the call gate validates against exactly those at dispatch and
 * an undeclared one is refused there (`ADR-033`). A free-text name is
 * still allowed: the catalogue may be unreadable, and refusing to let
 * the operator type what they mean would be this screen inventing a
 * rule the backend does not have.
 */
function InputsEditor({
  step,
  usable,
  declaredInputs,
  onPatch,
}: {
  step: WorkflowStep;
  usable: ReturnType<typeof whatThisStepCanUse>;
  declaredInputs: ActionInputField[] | undefined;
  onPatch: (patch: Partial<WorkflowStep>) => void;
}) {
  const [newName, setNewName] = useState('');
  const inputs = step.inputs ?? {};
  const names = Object.keys(inputs);
  const unused = (declaredInputs ?? []).filter((declared) => !names.includes(declared.name));

  function setInput(name: string, value: unknown) {
    onPatch({ inputs: { ...inputs, [name]: value } });
  }

  function removeInput(name: string) {
    const next = { ...inputs };
    delete next[name];
    onPatch({ inputs: next });
  }

  return (
    <div className="wf-inputs" data-testid="workflow-inspector-inputs">
      {names.length === 0 && (
        <span className="item-row-meta">
          Nothing is passed to this Action yet.
        </span>
      )}
      {names.map((name) => {
        const declared = (declaredInputs ?? []).find((candidate) => candidate.name === name);
        const value = inputs[name];
        return (
          <div className="wf-input-row" key={name}>
            <span className="wf-input-name">
              <code>{name}</code>
              {declaredInputs !== undefined && declared === undefined && (
                <span className="badge badge-warning" title="The call gate refuses an input the Action does not declare.">
                  not declared
                </span>
              )}
              {declared?.required && <span className="badge">required</span>}
            </span>
            <WiredValue
              value={typeof value === 'string' ? value : JSON.stringify(value ?? '')}
              usable={usable}
              placeholder={declared?.description || 'a value, or wire it to an earlier step'}
              testId={`workflow-input-${name}`}
              onChange={(next) => setInput(name, next)}
            />
            <button
              type="button"
              className="btn btn-danger"
              data-testid={`workflow-input-remove-${name}`}
              onClick={() => removeInput(name)}
            >
              Remove
            </button>
          </div>
        );
      })}

      <div className="wf-input-add">
        {unused.length > 0 && (
          <select
            className="input"
            data-testid="workflow-input-add-declared"
            value=""
            onChange={(event) => { if (event.target.value) setInput(event.target.value, ''); }}
          >
            <option value="">add one this Action declares…</option>
            {unused.map((declared) => (
              <option key={declared.name} value={declared.name}>
                {declared.name}{declared.required ? ' (required)' : ''}
              </option>
            ))}
          </select>
        )}
        <input
          className="input"
          placeholder="or a name of your own"
          data-testid="workflow-input-add-name"
          value={newName}
          onChange={(event) => setNewName(event.target.value)}
        />
        <button
          type="button"
          className="btn"
          data-testid="workflow-input-add"
          disabled={!newName.trim() || names.includes(newName.trim())}
          onClick={() => { setInput(newName.trim(), ''); setNewName(''); }}
        >
          Add
        </button>
      </div>
    </div>
  );
}
