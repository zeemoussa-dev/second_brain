import { useState } from 'react';
import { refusalText } from '../auth/SignInScreen';
import { publishSpecialists, saveRoutingConditions } from '../hermes-ops/client';

export interface RoutingEdge {
  from: string;
  to: string;
  when: string | null;
  declared: boolean;
}

export interface EdgeTarget {
  id: string;
  name: string;
  description: string;
}

/** Writing the `when` on one agent's specialist edges (`REQ-SB-102`).
 *
 * **Each specialist's own description sits beside its field.** The
 * condition is the operator's business judgement, not something this
 * app can derive — but almost all of what they need to make it is
 * already written on the child agent, and making them hold nine agents
 * in their head while typing is how twenty-three of these go unwritten.
 * "Use this" copies the description in as a starting point; it is
 * offered, never applied for them.
 *
 * **Saving and publishing are two buttons on purpose.** Saving records
 * the intent here. Publishing rewrites a live agent's SOUL.md, which is
 * a behaviour change on something currently answering, so it is a
 * separate, deliberate act on one named agent — never a sweep over all
 * of them.
 */
export function RoutingEditor({
  parent,
  edges,
  targets,
  onSaved,
}: {
  parent: string;
  edges: RoutingEdge[];
  targets: Map<string, EdgeTarget>;
  onSaved: () => void;
}) {
  const [draft, setDraft] = useState<Record<string, string>>(() =>
    Object.fromEntries(edges.map((edge) => [edge.to, edge.when ?? ''])),
  );
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  const unsaved = edges.some((edge) => (draft[edge.to] ?? '') !== (edge.when ?? ''));
  const anyWritten = edges.some((edge) => (draft[edge.to] ?? '').trim());

  async function run(work: () => Promise<unknown>, said: string) {
    setFailure(null);
    setNote(null);
    setBusy(true);
    try {
      await work();
      setNote(said);
      onSaved();
    } catch (error) {
      setFailure(refusalText(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="routing-editor" data-testid={`routing-editor-${parent}`}>
      <h3>
        <code>{parent}</code>{' '}
        <span className="auth-note">
          {edges.length} specialist{edges.length === 1 ? '' : 's'}
        </span>
      </h3>

      {edges.map((edge) => {
        const target = targets.get(edge.to);
        return (
          <div className="routing-edge" key={edge.to}>
            <label className="auth-field">
              <span>
                Go to <code>{edge.to}</code> when…
              </span>
              <input
                data-testid={`routing-when-${parent}-${edge.to}`}
                value={draft[edge.to] ?? ''}
                placeholder="the ask is about…"
                onChange={(event) =>
                  setDraft((d) => ({ ...d, [edge.to]: event.target.value }))
                }
              />
            </label>
            {target?.description && (
              <p className="auth-note routing-edge-desc">
                {target.description}{' '}
                <button
                  type="button"
                  className="routing-use"
                  onClick={() =>
                    setDraft((d) => ({
                      ...d,
                      [edge.to]: `the ask is about ${target.description.replace(/\.$/, '')}`,
                    }))
                  }
                >
                  use this
                </button>
              </p>
            )}
          </div>
        );
      })}

      {failure && <p className="auth-refusal" role="alert">{failure}</p>}
      {note && <p className="profile-done" role="status">{note}</p>}

      <div className="routing-actions">
        <button
          type="button"
          className="auth-primary"
          data-testid={`routing-save-${parent}`}
          disabled={busy || !unsaved}
          onClick={() =>
            void run(
              () => saveRoutingConditions(parent, draft),
              'Saved. Not in the agent’s prompt yet — publish to put it there.',
            )
          }
        >
          {busy ? 'Saving…' : 'Save conditions'}
        </button>
        <button
          type="button"
          data-testid={`routing-publish-${parent}`}
          disabled={busy || unsaved || !anyWritten}
          title={
            unsaved
              ? 'Save first — publishing writes what is saved, not what is typed.'
              : `Write these into ${parent}'s SOUL.md`
          }
          onClick={() =>
            void run(
              () => publishSpecialists(parent),
              `Written into ${parent}'s soul. That agent's prompt has changed.`,
            )
          }
        >
          Publish into {parent}’s soul
        </button>
      </div>
      {unsaved && (
        <p className="auth-note">
          Publishing is disabled until you save: it writes what is stored, not what is on
          screen, and a button that quietly published the old text would be worse than one
          that waits.
        </p>
      )}
    </div>
  );
}
