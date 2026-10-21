import type { WorkflowStep } from './workflowsApiClient';

// Reading a Workflow's wiring without running it (`REQ-SB-103`,
// `ADR-061`). The canvas draws edges from this and the inspector
// validates against it.
//
// **This mirrors the backend's `step_references.py` and is not the
// authority.** The run engine resolves references at dispatch and
// refuses the step if it cannot, which is what actually protects a run.
// What this adds is the same answer at AUTHORING time, where it can
// still be fixed -- a reference that only fails when a customer is
// waiting is a reference nobody found in time.

/** Same shape the backend accepts: a reference is the WHOLE value, not
 *  a fragment inside a longer string. Interpolating into prose is
 *  deliberately unsupported there, so offering it here would invent a
 *  capability the app does not have. */
const WHOLE_VALUE_REFERENCE = /^\s*\{\{\s*([a-zA-Z0-9_.-]+)\s*\}\}\s*$/;

export function referencePathIn(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const matched = WHOLE_VALUE_REFERENCE.exec(value);
  return matched ? matched[1] : null;
}

export function referenceText(path: string): string {
  return `{{${path}}}`;
}

export interface ReferenceReading {
  /** Where it was written: an input's name, or `ask` for the question. */
  field: string;
  path: string;
  kind: 'request' | 'step' | 'unknown';
  /** The step id a `steps.…` reference names, whatever its state. */
  stepId: string | null;
  /** Null when the reference is fine. A sentence when it is not, in the
   *  same register the backend refuses in -- the operator should read
   *  one story about references, not two. */
  problem: string | null;
}

/** Every reference one step makes, read against the steps around it.
 *
 * `position` is this step's index in the documented order, and the
 * forward-reference check is the whole reason this takes it: a step may
 * only use a result from a step BEFORE it, because a later one has not
 * run. Reordering is what makes that happen, and it is silent --
 * dragging a step above the one it depends on breaks it, the canvas is
 * the only place that can say so before a run does.
 */
export function readReferences(step: WorkflowStep, steps: WorkflowStep[]): ReferenceReading[] {
  const position = steps.indexOf(step);
  const readings: ReferenceReading[] = [];

  const read = (field: string, value: unknown) => {
    const path = referencePathIn(value);
    if (path === null) return;
    readings.push({ field, path, ...classify(path, steps, position) });
  };

  read('ask', step.ask);
  for (const [name, value] of Object.entries(step.inputs ?? {})) read(name, value);
  return readings;
}

function classify(
  path: string, steps: WorkflowStep[], position: number,
): Pick<ReferenceReading, 'kind' | 'stepId' | 'problem'> {
  const parts = path.split('.');

  if (parts[0] === 'request') {
    if (parts.length !== 2) {
      return {
        kind: 'unknown', stepId: null,
        problem: 'A request reference names one value, like {{request.customer}}.',
      };
    }
    // Whether the run will actually carry that key is not knowable
    // here: it comes from the agent that recognised the ask. Reported
    // as fine, because guessing would make every request reference
    // look broken.
    return { kind: 'request', stepId: null, problem: null };
  }

  if (parts[0] === 'steps') {
    if (parts.length !== 3 || parts[2] !== 'result') {
      return {
        kind: 'unknown', stepId: null,
        problem: "A step reference names a step's result, like {{steps.find.result}}.",
      };
    }
    const stepId = parts[1];
    const target = steps.findIndex((candidate) => candidate.id === stepId);
    if (target === -1) {
      return {
        kind: 'step', stepId,
        problem: `No step in this Workflow is called '${stepId}'.`,
      };
    }
    if (target >= position && position !== -1) {
      return {
        kind: 'step', stepId,
        problem: target === position
          ? 'A step cannot use its own result.'
          : `'${stepId}' runs after this step, so it has produced nothing yet. `
            + 'Move it earlier, or point at a step above this one.',
      };
    }
    return { kind: 'step', stepId, problem: null };
  }

  return {
    kind: 'unknown', stepId: null,
    problem: 'A reference begins with `request.` or `steps.`.',
  };
}

/** Every reference across the Workflow that is broken, for the one-line
 *  summary above the canvas. A count is what makes a problem visible
 *  when the step carrying it is scrolled off. */
export function brokenReferences(steps: WorkflowStep[]): Array<ReferenceReading & { step: WorkflowStep }> {
  return steps.flatMap((step) =>
    readReferences(step, steps)
      .filter((reading) => reading.problem !== null)
      .map((reading) => ({ ...reading, step })),
  );
}

/** What a step could be wired to: every step before it, plus whatever
 *  the request already mentions anywhere in this Workflow.
 *
 *  Only earlier steps are offered, because only they can have run. The
 *  picker therefore cannot create a forward reference at all -- the
 *  validation above exists for the ones reordering creates afterwards.
 */
export function whatThisStepCanUse(
  step: WorkflowStep, steps: WorkflowStep[],
): { steps: WorkflowStep[]; requestKeys: string[] } {
  const position = steps.indexOf(step);
  const earlier = position === -1 ? steps : steps.slice(0, position);
  const requestKeys = new Set<string>();
  for (const candidate of steps) {
    for (const reading of readReferences(candidate, steps)) {
      if (reading.kind === 'request') requestKeys.add(reading.path.split('.')[1]);
    }
  }
  return {
    steps: earlier.filter((candidate) => candidate.id !== ''),
    requestKeys: [...requestKeys].sort(),
  };
}
