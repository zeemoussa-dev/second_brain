import { useState } from 'react';
import type { WorkflowStep, WorkflowStepKind } from './workflowsApiClient';
import { readReferences, referencePathIn } from './workflowReferences';

/** The Workflow as a picture you can rearrange (operator, 2026-10-21:
 * "I am a visual person, I love drag and drop, I need to see the
 * workflow visually").
 *
 * **A chain, not a graph, because a Workflow is a chain.** There is no
 * branching and no repetition in one (`ADR-034`), so a canvas that
 * offered free placement would be drawing a shape the thing cannot
 * have. What there IS to see is the order, what each step is, and
 * which steps feed which — so the cards sit in documented order and
 * the edges carry the data flow.
 *
 * **Dragging reorders; the arrow keys and the move buttons do the same
 * thing.** Drag-and-drop is what was asked for and it is not the only
 * way in: a pointer gesture is unusable with a keyboard, and the
 * existing controls already worked. Both call one reorder.
 *
 * **A step keeps its id when it moves.** `ADR-034` addresses a step by
 * id and never by position, so a run already under way still means the
 * same step. Re-keying on drop would quietly re-aim it.
 *
 * **A broken reference is drawn broken.** Dragging a step above the one
 * it depends on is silent otherwise — the run refuses later, when
 * somebody is waiting. Here it goes red the moment it happens.
 */

const KIND_LABEL: Record<WorkflowStepKind, string> = {
  action: 'Action',
  agent: 'Agent',
  human: 'Person',
};

/** One glyph per kind, from the Material Symbols font the rest of the
 *  app already uses. Shape AND word, never shape alone: a legend you
 *  have to learn is a legend nobody reads. */
const KIND_ICON: Record<WorkflowStepKind, string> = {
  action: 'bolt',
  agent: 'smart_toy',
  human: 'person_raised_hand',
};

function kindOf(step: WorkflowStep): WorkflowStepKind {
  return (step.kind ?? 'action') as WorkflowStepKind;
}

/** What this step is, in the one line the card shows. Named by what it
 *  does rather than by its id, because a chain of ids reads as nothing
 *  until you already know the Workflow.
 *
 *  A question that IS a reference is described rather than quoted: the
 *  literal `{{steps.draft.result}}` as a card's headline reads as
 *  syntax, not as what the person will be shown. The wiring row below
 *  it already says which step it comes from. */
function headline(step: WorkflowStep, steps: WorkflowStep[]): string {
  const kind = kindOf(step);
  if (kind === 'agent') return step.agent_id || 'no agent named yet';
  if (kind === 'human') {
    if (!step.ask) return 'no question yet';
    const path = referencePathIn(step.ask);
    if (path === null) return step.ask;
    const fromStep = path.startsWith('steps.') ? path.split('.')[1] : null;
    return fromStep === null
      ? 'asks with what the request was about'
      : `asks with whatever step ${stepNumberOf(steps, fromStep)} comes back with`;
  }
  return step.action_id || 'no action named yet';
}

export function WorkflowCanvas({
  steps,
  selectedIndex,
  onSelect,
  onReorder,
  onAdd,
  onRemove,
}: {
  steps: WorkflowStep[];
  selectedIndex: number | null;
  onSelect: (index: number) => void;
  onReorder: (from: number, to: number) => void;
  onAdd: (kind: WorkflowStepKind) => void;
  onRemove: (index: number) => void;
}) {
  const [dragging, setDragging] = useState<number | null>(null);
  const [dropBefore, setDropBefore] = useState<number | null>(null);

  function finishDrop(to: number) {
    if (dragging !== null && to !== dragging) {
      // A drop BEFORE index `to` lands at `to - 1` when the card came
      // from above it, because removing it first shifts everything up.
      onReorder(dragging, dragging < to ? to - 1 : to);
    }
    setDragging(null);
    setDropBefore(null);
  }

  const gap = (index: number) => (
    <div
      className={dropBefore === index ? 'wf-gap wf-gap--armed' : 'wf-gap'}
      data-testid={`workflow-canvas-gap-${index}`}
      onDragOver={(event) => { event.preventDefault(); setDropBefore(index); }}
      onDragLeave={() => setDropBefore((at) => (at === index ? null : at))}
      onDrop={(event) => { event.preventDefault(); finishDrop(index); }}
    >
      <span className="wf-gap-line" />
    </div>
  );

  return (
    <div className="wf-canvas" data-testid="workflow-canvas">
      <div className="wf-rail">
        <span className="wf-rail-label">The ask arrives</span>
      </div>

      {steps.length === 0 && (
        <p className="item-row-meta" data-testid="workflow-canvas-empty">
          No steps yet. Add one below — a Workflow with no steps cannot be run, and the app
          refuses to start one.
        </p>
      )}

      {steps.map((step, index) => {
        const kind = kindOf(step);
        const readings = readReferences(step, steps);
        const broken = readings.filter((reading) => reading.problem !== null);
        const feeds = readings.filter((reading) => reading.kind === 'step' && !reading.problem);
        return (
          <div key={step.id || `new-${index}`}>
            {gap(index)}
            <div
              className={[
                'wf-card',
                `wf-card--${kind}`,
                selectedIndex === index ? 'wf-card--selected' : '',
                dragging === index ? 'wf-card--dragging' : '',
                broken.length > 0 ? 'wf-card--broken' : '',
              ].filter(Boolean).join(' ')}
              data-testid={`workflow-card-${index}`}
              draggable
              onDragStart={() => setDragging(index)}
              onDragEnd={() => { setDragging(null); setDropBefore(null); }}
              onClick={() => onSelect(index)}
              // The card is a button in everything but tag: clicking it
              // selects, and a keyboard must be able to do the same.
              // Arrow keys move it, which is the keyboard's drag.
              role="button"
              tabIndex={0}
              aria-current={selectedIndex === index}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  onSelect(index);
                } else if (event.key === 'ArrowUp' && event.altKey) {
                  event.preventDefault();
                  onReorder(index, Math.max(0, index - 1));
                } else if (event.key === 'ArrowDown' && event.altKey) {
                  event.preventDefault();
                  onReorder(index, Math.min(steps.length - 1, index + 1));
                }
              }}
            >
              <span className="wf-card-grip material-symbols-outlined" aria-hidden="true">
                drag_indicator
              </span>
              <span className="wf-card-position">{index + 1}</span>
              <span className="wf-card-body">
                <span className="wf-card-kind">
                  <span className="material-symbols-outlined" aria-hidden="true">
                    {KIND_ICON[kind]}
                  </span>
                  {KIND_LABEL[kind]}
                </span>
                <span className="wf-card-headline">{headline(step, steps)}</span>
                {step.description && (
                  <span className="item-row-meta">{step.description}</span>
                )}
                <span className="wf-card-wiring">
                  {feeds.map((reading) => (
                    <span className="wf-wire" key={`${reading.field}:${reading.path}`}>
                      <span className="material-symbols-outlined" aria-hidden="true">
                        arrow_downward
                      </span>
                      {reading.field} ← step {stepNumberOf(steps, reading.stepId)}
                    </span>
                  ))}
                  {readings.filter((r) => r.kind === 'request' && !r.problem).map((reading) => (
                    <span className="wf-wire" key={`${reading.field}:${reading.path}`}>
                      {reading.field} ← the ask
                    </span>
                  ))}
                  {kind === 'action' && step.needs_confirmation && (
                    <span className="badge badge-warning">Asks you first</span>
                  )}
                  {kind === 'human' && step.allows_edit && (
                    <span className="badge">They may edit it</span>
                  )}
                </span>
                {broken.map((reading) => (
                  <span
                    className="wf-card-broken"
                    key={`${reading.field}:${reading.path}`}
                    data-testid={`workflow-card-${index}-broken`}
                  >
                    <span className="material-symbols-outlined" aria-hidden="true">link_off</span>
                    <code>{reading.field}</code> uses <code>{`{{${reading.path}}}`}</code> —{' '}
                    {reading.problem}
                  </span>
                ))}
              </span>
              <button
                type="button"
                className="btn btn-danger wf-card-remove"
                data-testid={`workflow-card-remove-${index}`}
                onClick={(event) => { event.stopPropagation(); onRemove(index); }}
              >
                Remove
              </button>
            </div>
          </div>
        );
      })}

      {gap(steps.length)}

      <div className="wf-rail">
        <span className="wf-rail-label">The report goes back</span>
      </div>

      <div className="wf-palette" data-testid="workflow-canvas-palette">
        {(['action', 'agent', 'human'] as WorkflowStepKind[]).map((kind) => (
          <button
            type="button"
            className="btn wf-palette-button"
            key={kind}
            data-testid={`workflow-canvas-add-${kind}`}
            onClick={() => onAdd(kind)}
          >
            <span className="material-symbols-outlined" aria-hidden="true">{KIND_ICON[kind]}</span>
            Add {kind === 'human' ? 'a question for a person' : `${KIND_LABEL[kind].toLowerCase()} step`}
          </button>
        ))}
      </div>
    </div>
  );
}

/** A step's position for a reader, from its id. The card shows "step 2"
 *  rather than the id because position is what the eye is following
 *  down the chain; the id is the inspector's business. */
function stepNumberOf(steps: WorkflowStep[], stepId: string | null): string {
  const at = steps.findIndex((step) => step.id === stepId);
  return at === -1 ? `'${stepId}'` : String(at + 1);
}
