import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router';
import { apiFetch } from '../api/client';
import { refusalText } from '../features/auth/SignInScreen';
import { useAuth } from '../features/auth/AuthGate';
import {
  ActionAssignmentEditor,
  SkillsEditor,
} from '../features/settings/AgentFlowEditors';
import { RoutingEditor } from '../features/settings/RoutingEditor';
import type { EdgeTarget } from '../features/settings/RoutingEditor';

interface Edge { from: string; to: string; when: string | null; declared: boolean }
interface AgentNode { id: string; name: string; routes_to: string[]; may_call: string[]; is_entry: boolean }
interface ActionRow { id: string; description: string; callers: string[]; is_blocked: boolean; blocked_reason: string; touches: string | null }
interface Door { label: string; source: string; chat_id: string; reaches: string | null }
interface Gap { kind: string; subject: string; says: string }
interface FlowMap {
  entry_points: Door[]; agents: AgentNode[]; edges: Edge[];
  actions: ActionRow[]; gaps: Gap[];
}

/** Where a gap of this kind is put right.
 *
 * `to` is a route to the screen that owns it; `null` means it is fixed
 * on THIS page and `act` scrolls to the control. Returning `null`
 * overall is honest too -- some gaps are a statement about the install
 * rather than a thing with an owner, and inventing a destination for
 * those would send someone to a screen that cannot help. */
function whereToFix(
  gap: Gap, agentId: string,
): { label: string; to: string | null; act?: () => void } | null {
  const scrollToRouting = () => {
    document
      .querySelector('[data-testid="agent-flow-routing"]')
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  // `parent -> child`: the condition belongs to the PARENT, wherever
  // the gap is being read from.
  const parent = gap.subject.includes(' -> ') ? gap.subject.split(' -> ')[0].trim() : null;

  switch (gap.kind) {
    case 'edge_without_a_condition':
    case 'condition_for_a_non_specialist':
      return parent === null || parent === agentId
        ? { label: 'Say when, below', to: null, act: scrollToRouting }
        : { label: `Say when on ${parent}`, to: `/flow/${encodeURIComponent(parent)}` };
    case 'entry_point_not_declared':
    case 'entry_point_drifted':
    case 'entry_point_reaches_unknown_agent':
      return { label: 'Declare the door', to: '/entry-points' };
    case 'action_nobody_may_call':
    case 'action_without_an_implementation':
      return { label: 'Open this Action', to: '/settings/actions' };
    case 'workflow_step_names_a_missing_action':
      return { label: 'Open Workflows', to: '/settings/workflows' };
    case 'agent_nothing_reaches':
      // Nothing routes here, so the fix is on whichever agent SHOULD
      // hand work down -- which this app cannot guess. The agent's own
      // "Works for" is the field that changes it.
      return { label: 'Set who it works for', to: `/agents/${encodeURIComponent(agentId)}/profile` };
    default:
      return null;
  }
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
  const { may } = useAuth();
  const canEdit = may('manage_agents');
  const [map, setMap] = useState<FlowMap | null>(null);
  const [targets, setTargets] = useState<Map<string, EdgeTarget>>(new Map());
  const [failure, setFailure] = useState<string | null>(null);
  const [reloads, setReloads] = useState(0);

  useEffect(() => {
    apiFetch<FlowMap>('/hermes/flow-map')
      .then(setMap)
      .catch((error) => setFailure(refusalText(error)));
  }, [agentId, reloads]);

  // Each specialist's own description, so a condition is written with what
  // that agent says about itself in front of the operator rather than from
  // memory. A failure here costs the hint, never the editor.
  useEffect(() => {
    apiFetch<{ agents?: EdgeTarget[] } | EdgeTarget[]>('/agents')
      .then((answer) => {
        const list = Array.isArray(answer) ? answer : (answer.agents ?? []);
        setTargets(new Map(list.map((candidate) => [candidate.id, candidate])));
      })
      .catch(() => setTargets(new Map()));
  }, []);

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
  // Each agent that hands work down to this one, with that parent's
  // WHOLE routing — the save replaces a parent's condition map
  // wholesale, so a partial set here would delete its other routes.
  const parentsRoutingHere = [...new Set(reachedBy.map((edge) => edge.from))]
    .sort()
    .map((parentId) => ({
      parentId,
      edges: map.edges.filter((edge) => edge.from === parentId),
    }));
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
                  {edge.when ? (
                    `When: ${edge.when}`
                  ) : (
                    <>
                      No condition said — nothing records why an ask should go here.{' '}
                      {canEdit && (
                        <button
                          type="button"
                          className="routing-use"
                          onClick={() => {
                            document
                              .getElementById(`routing-${agent.id}`)
                              ?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            document
                              .querySelector<HTMLInputElement>(
                                `[data-testid="routing-when-${agent.id}-${edge.to}"]`,
                              )
                              ?.focus({ preventScroll: true });
                          }}
                        >
                          say when
                        </button>
                      )}
                    </>
                  )}
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
            {mine.map((gap, index) => {
              const fix = whereToFix(gap, agent.id);
              return (
                <li key={`${gap.kind}-${index}`}>
                  <strong>{gap.subject}</strong>
                  <div className="auth-note">{gap.says}</div>
                  {/* Every gap says where it is fixed (operator,
                      2026-10-24: "for the gaps, what's the value if I
                      can't fix it"). A detector that only names a
                      problem spends the reader's attention and gives
                      nothing back; the one thing it knows that they do
                      not is which screen owns the thing it just
                      checked. */}
                  {fix && (
                    <div className="flow-gap-fix">
                      {fix.to === null ? (
                        <button
                          type="button"
                          className="auth-link-button"
                          data-testid={`gap-fix-${index}`}
                          onClick={fix.act}
                        >
                          {fix.label}
                        </button>
                      ) : (
                        <Link to={fix.to} data-testid={`gap-fix-${index}`}>{fix.label}</Link>
                      )}
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {canEdit && (
        <section>
          <h2>Change this agent's flow</h2>
          <p className="auth-note">
            Routes and Action assignment take effect at once. A route's <em>when</em> is saved
            here and only reaches the agent's prompt when you publish it.
          </p>
          {/* No specialist editor here, deliberately (operator,
              2026-10-24: "The Flow has nothing to do with UI except
              that depends_on as enable inside the Agent View -- The
              Flow is pure Hermes").

              `depends_on` is edited in ONE place, the Agent view's own
              "Relays to" checklist, which writes that agent's own file.
              The editor that used to sit here wrote the link onto the
              WRONG agent -- it took `routes_to` (the children the map
              derived from everyone else's `depends_on`) and PATCHed it
              into this agent's own `depends_on`, which says the
              opposite thing and put the link on the wrong node. Two
              editors for one fact is how that survived unnoticed. */}

          {/* The condition, on the page where the route was just created
              (operator, 2026-10-24: "I can't find When I change Primary to
              Call Specialist where to set the When"). Adding a specialist
              here used to leave a route with no condition and a sentence
              pointing at another page, where this agent's editor is one of
              dozens stacked under a single heading. Keyed by the edge set so
              a specialist added a second ago gets its own empty field rather
              than waiting for a remount. */}
          <div data-testid="agent-flow-routing">
            {sendsTo.length > 0 && (
              <RoutingEditor
                key={sendsTo.map((edge) => edge.to).join('|')}
                parent={agent.id}
                edges={sendsTo}
                targets={targets}
                onSaved={() => setReloads((n) => n + 1)}
              />
            )}

            {/* The route INTO this agent, editable from here (operator,
                2026-10-24: "I can't edit the when inside the Adnoc agent
                itself, yet it shows what's missing and I can't do
                anything about it").

                The condition lives on the PARENT -- `{parent: {child:
                when}}` -- so this is the parent's own routing, shown
                where the person noticed it was missing and labelled as
                the parent's so nobody thinks otherwise.

                **Seeded with ALL of that parent's edges, not just the
                one into this agent**, and that is not cosmetic: the PUT
                replaces a parent's whole condition map with what it is
                sent, so an editor holding one edge would delete every
                other condition that parent has the moment it saved. */}
            {parentsRoutingHere.map(({ parentId, edges }) => (
              <div key={`into-${parentId}`} className="agent-editor">
                <h3>
                  How work reaches this agent — <code>{parentId}</code>&apos;s routing
                </h3>
                <p className="auth-note">
                  <code>{parentId}</code> hands work down to this agent, so the <em>when</em>
                  {' '}belongs to <code>{parentId}</code>. Its other routes are shown because
                  saving writes all of them at once.
                </p>
                <RoutingEditor
                  key={edges.map((edge) => edge.to).join('|')}
                  parent={parentId}
                  edges={edges}
                  targets={targets}
                  onSaved={() => setReloads((n) => n + 1)}
                />
              </div>
            ))}
          </div>
          <ActionAssignmentEditor
            agentId={agent.id}
            actions={map.actions}
            onChanged={() => setReloads((n) => n + 1)}
          />
          <SkillsEditor agentId={agent.id} onChanged={() => setReloads((n) => n + 1)} />
        </section>
      )}

      <p className="auth-note">
        Want to see what it actually did, rather than what it may do?{' '}
        <Link to="/agent-activity">Agent Activity</Link> reads a real session step by step.
      </p>
    </>
  );
}
