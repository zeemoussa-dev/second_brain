import { useEffect, useState } from 'react';
import { refusalText } from '../auth/SignInScreen';
import {
  deploySkill,
  fetchAgentSkills,
  fetchAllSkills,
  setAllowedCallers,
  setSpecialists,
  undeploySkill,
} from '../hermes-ops/client';
import type { SkillSummary } from '../hermes-ops/client';

interface ActionRow { id: string; description: string; callers: string[] }

/** Shared runner: the backend's own sentence on failure, and a reload
 * afterwards rather than a local patch, so what is shown comes from the
 * store instead of from a guess about what the write did. */
function useWriter(onChanged: () => void) {
  const [busy, setBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  async function run(work: () => Promise<unknown>, said?: string) {
    setFailure(null);
    setNote(null);
    setBusy(true);
    try {
      const answer = await work();
      const detail = (answer as { detail?: string } | null)?.detail;
      setNote(detail ?? said ?? 'Saved.');
      onChanged();
    } catch (error) {
      setFailure(refusalText(error));
    } finally {
      setBusy(false);
    }
  }
  return { busy, failure, note, run };
}

function Feedback({ failure, note }: { failure: string | null; note: string | null }) {
  return (
    <>
      {failure && <p className="auth-refusal" role="alert">{failure}</p>}
      {note && <p className="profile-done" role="status">{note}</p>}
    </>
  );
}

/** Add or remove a specialist — the SHAPE of the flow.
 *
 * Kept visibly separate from the `when` beside it, because they are
 * different things in different places: the edge lives in Hermes'
 * registry and the condition is this app's annotation about it. Removing
 * an edge here leaves its condition stored but unused rather than
 * deleting it, so putting the route back does not mean rewriting the
 * sentence — and an orphaned condition is reported by the map as a gap
 * rather than quietly applying to nothing.
 */
export function SpecialistsEditor({
  agentId, current, candidates, onChanged,
}: {
  agentId: string; current: string[]; candidates: string[]; onChanged: () => void;
}) {
  const { busy, failure, note, run } = useWriter(onChanged);
  const [picked, setPicked] = useState('');
  const addable = candidates.filter((id) => id !== agentId && !current.includes(id));

  return (
    <div className="agent-editor" data-testid="specialists-editor">
      <h3>Who this agent can hand work to</h3>
      {current.length === 0 ? (
        <p className="auth-note">No specialists — it answers everything itself.</p>
      ) : (
        <ul className="agent-editor-list">
          {current.map((id) => (
            <li key={id}>
              <code>{id}</code>
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void run(
                    () => setSpecialists(agentId, current.filter((other) => other !== id)),
                    `${id} is no longer a specialist of ${agentId}. Its condition is kept, unused.`,
                  )
                }
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="agent-editor-add">
        <select value={picked} onChange={(event) => setPicked(event.target.value)}>
          <option value="">add a specialist…</option>
          {addable.map((id) => <option key={id} value={id}>{id}</option>)}
        </select>
        <button
          type="button"
          disabled={busy || !picked}
          onClick={() =>
            void run(
              () => setSpecialists(agentId, [...current, picked]),
              `${picked} added. Say when to use it on the map, then publish.`,
            ).then(() => setPicked(''))
          }
        >
          Add
        </button>
      </div>
      <p className="auth-note">
        This changes the agent's registry entry, not its prompt. Publish on{' '}
        <strong>The Flow</strong> to write it into the soul.
      </p>
      <Feedback failure={failure} note={note} />
    </div>
  );
}

/** Which Actions this agent may call.
 *
 * Writes `allowed_callers` on the Action, because that IS the field —
 * assigning an Action to an agent and allowing an agent to call an
 * Action are one fact read from two ends, and a second store for the
 * other end is how the two come to disagree.
 *
 * An Action open to everyone (`*`) is shown as such and NOT silently
 * rewritten into a list naming this agent: narrowing a wildcard would
 * quietly revoke it from every other agent on the install.
 */
export function ActionAssignmentEditor({
  agentId, actions, onChanged,
}: {
  agentId: string; actions: ActionRow[]; onChanged: () => void;
}) {
  const { busy, failure, note, run } = useWriter(onChanged);

  return (
    <div className="agent-editor" data-testid="action-assignment-editor">
      <h3>What this agent may do</h3>
      {actions.length === 0 ? (
        <p className="auth-note">There are no Actions in the catalogue yet.</p>
      ) : (
        <ul className="agent-editor-list">
          {actions.map((action) => {
            const open = action.callers.includes('*');
            const allowed = open || action.callers.includes(agentId);
            return (
              <li key={action.id}>
                <code>{action.id}</code>
                {open ? (
                  <span className="auth-note">open to every agent</span>
                ) : (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      void run(() =>
                        setAllowedCallers(
                          action.id,
                          allowed
                            ? action.callers.filter((c) => c !== agentId)
                            : [...action.callers, agentId],
                        ),
                      )
                    }
                  >
                    {allowed ? 'Take away' : 'Allow'}
                  </button>
                )}
              </li>
            );
          })}
        </ul>
      )}
      <p className="auth-note">
        An Action open to every agent is left alone here — narrowing it would take it away
        from everyone else at the same time.
      </p>
      <Feedback failure={failure} note={note} />
    </div>
  );
}

/** Which Skills are deployed into this agent's Hermes profile.
 *
 * A real deploy: it copies the Skill's current content into the
 * profile. That is why the backend's own sentence is shown verbatim
 * rather than a generic "saved" — "was already deployed; nothing
 * changed" and "is now deployed" are different facts and the operator
 * should see which happened.
 */
export function SkillsEditor({ agentId, onChanged }: { agentId: string; onChanged: () => void }) {
  const { busy, failure, note, run } = useWriter(onChanged);
  const [all, setAll] = useState<SkillSummary[] | null>(null);
  const [mine, setMine] = useState<SkillSummary[] | null>(null);
  const [reloads, setReloads] = useState(0);

  useEffect(() => {
    Promise.all([fetchAllSkills(), fetchAgentSkills(agentId)])
      .then(([every, deployed]) => { setAll(every); setMine(deployed); })
      .catch(() => { setAll([]); setMine([]); });
  }, [agentId, reloads]);

  const again = () => { setReloads((n) => n + 1); onChanged(); };

  if (!all || !mine) return <div className="agent-editor"><h3>Skills</h3><p>Loading…</p></div>;

  const deployed = new Set(mine.map((s) => s.id));

  return (
    <div className="agent-editor" data-testid="skills-editor">
      <h3>Skills deployed into its profile ({mine.length})</h3>
      <ul className="agent-editor-list">
        {all.map((skill) => (
          <li key={skill.id}>
            <code>{skill.id}</code>
            {deployed.has(skill.id) && <span className="badge badge-success">deployed</span>}
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                void run(() =>
                  deployed.has(skill.id)
                    ? undeploySkill(agentId, skill.id)
                    : deploySkill(agentId, skill.id),
                ).then(again)
              }
            >
              {deployed.has(skill.id) ? 'Remove' : 'Deploy'}
            </button>
          </li>
        ))}
      </ul>
      <p className="auth-note">
        Deploying copies the Skill's current content into this agent's real Hermes profile.
        Re-deploying an updated Skill is how a profile stops running an old copy.
      </p>
      <Feedback failure={failure} note={note} />
    </div>
  );
}
