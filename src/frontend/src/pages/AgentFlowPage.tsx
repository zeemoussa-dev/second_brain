import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { apiFetch } from '../api/client';
import { refusalText } from '../features/auth/SignInScreen';

interface Edge { from: string; to: string; when: string | null; declared: boolean }
interface AgentNode { id: string; name: string; routes_to: string[]; may_call: string[]; is_entry: boolean }
interface ActionRow { id: string; description: string; callers: string[]; is_blocked: boolean; blocked_reason: string; touches: string | null }
interface Door { label: string; source: string; chat_id: string; reaches: string | null }
interface Gap { kind: string; subject: string; says: string }
interface FlowMap {
  entry_points: Door[]; agents: AgentNode[]; edges: Edge[];
  actions: ActionRow[]; gaps: Gap[];
}

/** REQ-SB-102 — one agent's own slice of the flow: how an ask reaches
 * it, where it sends one on, what it may do, and what is missing.
 *
 * **Reached from the map, and the map is 42 agents wide.** The whole
 * picture answers "how does this install hang together"; this answers
 * "what is wrong with THIS one", which is the question an operator has
 * while something is misbehaving. The operator asked for both, and they
 * are different questions rather than two sizes of the same one.
 *
 * **Gaps are filtered to this agent, by subject.** A page about one
 * agent that lists the whole install's problems makes the operator do
 * the filtering, which is the work they came here to avoid.
 */
export function AgentFlowPage() {
  const { agentId = '' } = useParams();
  const [map, setMap] = useState<FlowMap | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<FlowMap>('/hermes/flow-map')
      .then(setMap)
      .catch((error) => setFailure(refusalText(error)));
  }, [agentId]);

  if (failure) return <><h1>{agentId}</h1><p className="auth-refusal" role="alert">{failure}</p></>;
  if (!map) return <><h1>{agentId}</h1><p>Reading the flow…</p></>;

  const agent = map.agents.find((a) => a.id === agentId);
  if (!agent) {
    return (
      <>
        <h1>{agentId}</h1>
        <p className="auth-note" data-testid="agent-flow-unknown">
          There is no agent with this id on the install. It may have been renamed or removed —
          the map is read fresh every time, so this is current, not cached.
        </p>
        <Link to="/flow">Back to the map</Link>
      </>
    );
  }

  const doorsIn = map.entry_points.filter((door) => door.reaches === agentId);
  const sendsTo = map.edges.filter((edge) => edge.from === agentId);
  const reachedBy = map.edges.filter((edge) => edge.to === agentId);
  const actions = map.actions.filter((action) => action.callers.includes(agentId));
  const mine = map.gaps.filter((gap) => gap.subject.includes(agentId));

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/flow">&larr; The map</Link></p>
      <h1>{agent.name}</h1>
      <p className="auth-note">
        <code>{agent.id}</code>
        {' · '}
        <Link to={`/agents/${encodeURIComponent(agent.id)}/profile`}>
          read its profile as it really is
        </Link>
      </p>

      <section>
        <h2>How an ask gets here</h2>
        {doorsIn.length === 0 && reachedBy.length === 0 ? (
          <p className="auth-note" data-testid="agent-flow-unreached">
            Nothing routes here. No outside door reaches this agent and no other agent sends
            it work — so it only ever runs if something calls it directly.
          </p>
        ) : (
          <ul className="flow-edges">
            {doorsIn.map((door) => (
              <li key={door.chat_id}>
                <span className="badge">{door.source}</span> <strong>{door.label}</strong> — an
                outside door opens straight onto this agent.
              </li>
            ))}
            {reachedBy.map((edge) => (
              <li key={edge.from} className={edge.declared ? '' : 'flow-edge-silent'}>
                <code>{edge.from}</code> sends work here
                <div className="auth-note">
                  {edge.when ? `When: ${edge.when}` : 'No condition said — that agent decides on its own.'}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Where it sends work on ({sendsTo.length})</h2>
        {sendsTo.length === 0 ? (
          <p className="auth-note">
            It has no specialists — whatever it is asked, it answers itself.
          </p>
        ) : (
          <ul className="flow-edges" data-testid="agent-flow-routes">
            {sendsTo.map((edge) => (
              <li key={edge.to} className={edge.declared ? '' : 'flow-edge-silent'}>
                <Link to={`/flow/${encodeURIComponent(edge.to)}`}><code>{edge.to}</code></Link>
                <div className="auth-note">
                  {edge.when ? `When: ${edge.when}` : 'No condition said — nothing records why an ask should go here.'}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>What it may do ({actions.length})</h2>
        {actions.length === 0 ? (
          <p className="auth-note">
            No Action allows this agent as a caller, so it cannot make this app do anything —
            it can only talk.
          </p>
        ) : (
          <table className="settings-table" data-testid="agent-flow-actions">
            <thead><tr><th>Action</th><th>Touches</th></tr></thead>
            <tbody>
              {actions.map((action) => (
                <tr key={action.id}>
                  <td>
                    <code>{action.id}</code>
                    {action.is_blocked && <> <span className="badge badge-danger">Blocked</span></>}
                    <div className="auth-note">{action.description}</div>
                    {action.is_blocked && action.blocked_reason && (
                      <div className="auth-note">{action.blocked_reason}</div>
                    )}
                  </td>
                  <td className="auth-note">{action.touches ?? 'nothing — no implementation'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>What is missing here ({mine.length})</h2>
        {mine.length === 0 ? (
          <p className="auth-note">
            Nothing this map can detect. Every route into and out of this agent says when to
            take it, and every Action it may call has something to perform it.
          </p>
        ) : (
          <ul className="flow-gaps" data-testid="agent-flow-gaps">
            {mine.map((gap, index) => (
              <li key={`${gap.kind}-${index}`}>
                <strong>{gap.subject}</strong>
                <div className="auth-note">{gap.says}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="auth-note">
        Want to see what it actually did, rather than what it may do?{' '}
        <Link to="/agent-activity">Agent Activity</Link> reads a real session step by step.
      </p>
    </>
  );
}
