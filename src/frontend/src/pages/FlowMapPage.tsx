import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { apiFetch } from '../api/client';
import { refusalText } from '../features/auth/SignInScreen';
import { useAuth } from '../features/auth/AuthGate';
import { FlowDiagram } from '../features/settings/FlowDiagram';
import { RoutingEditor } from '../features/settings/RoutingEditor';
import type { EdgeTarget } from '../features/settings/RoutingEditor';

interface Gap { kind: string; subject: string; says: string }
interface Door {
  label: string; source: string; chat_id: string;
  declared_agent: string | null; answered_by: string[];
  reaches: string | null; status: string;
}
interface AgentNode {
  id: string; name: string; type: string | null;
  routes_to: string[]; may_call: string[]; is_entry: boolean;
}
interface Edge { from: string; to: string; when: string | null; declared: boolean }
interface ActionRow {
  id: string; description: string; callers: string[];
  is_blocked: boolean; blocked_reason: string; touches: string | null;
}
interface WorkflowRow {
  id: string; request_kind: string | null;
  steps: Array<{ position: number; id: string | null; action_id: string | null; needs_confirmation: boolean }>;
}
interface FlowMap {
  entry_points: Door[]; agents: AgentNode[]; edges: Edge[];
  actions: ActionRow[]; workflows: WorkflowRow[]; gaps: Gap[];
  counts: Record<string, number>; caveat: string; unread: string[];
}

/** REQ-SB-102 — the flow, from the outside doors inwards.
 *
 * **The caveat is on the page, not in a tooltip.** A routing condition
 * is an instruction to a model, not an enforced branch, so this map
 * says what the install TELLS its agents — never what one will do. A
 * reader who misses that will trust a diagram that cannot promise what
 * they think it promises, so it is printed where it cannot be missed.
 *
 * **Gaps come first.** The operator asked for this to see gaps; putting
 * them after a diagram would make the diagram the point and the gaps
 * the footnote, which is backwards.
 */
export function FlowMapPage() {
  const { may } = useAuth();
  const canEditRouting = may('manage_agents');
  const [map, setMap] = useState<FlowMap | null>(null);
  const [targets, setTargets] = useState<Map<string, EdgeTarget>>(new Map());
  const [failure, setFailure] = useState<string | null>(null);
  const [reloads, setReloads] = useState(0);
  const [focus, setFocus] = useState<string | null>(null);

  useEffect(() => {
    apiFetch<FlowMap>('/hermes/flow-map')
      .then(setMap)
      .catch((error) => setFailure(refusalText(error)));
  }, [reloads]);

  // The specialists' own descriptions, so the operator writes each
  // condition with what that agent says about itself in front of them.
  useEffect(() => {
    apiFetch<{ agents?: EdgeTarget[] } | EdgeTarget[]>('/agents')
      .then((answer) => {
        const list = Array.isArray(answer) ? answer : (answer.agents ?? []);
        setTargets(new Map(list.map((a) => [a.id, a])));
      })
      .catch(() => setTargets(new Map()));
  }, []);

  if (failure) return <><h1>The flow</h1><p className="auth-refusal" role="alert">{failure}</p></>;
  if (!map) return <><h1>The flow</h1><p>Reading the install…</p></>;

  const agentsById = new Map(map.agents.map((a) => [a.id, a]));

  return (
    <>
      <h1>The flow</h1>
      <p className="text-muted">
        The outside doors into this install, the agents behind them, where each routes, and
        what each may do. Every line comes from a real record — nothing here is inferred
        from what an agent happened to do.
      </p>
      <p className="auth-note" data-testid="flow-caveat">{map.caveat}</p>

      {map.unread.length > 0 && (
        <p className="auth-refusal" role="alert" data-testid="flow-unread">
          Some of this could not be read, so the map is incomplete rather than empty:{' '}
          {map.unread.join('; ')}
        </p>
      )}

      {/* The picture comes before the lists: the operator asked to SEE
          the flow, and a diagram under three sections of prose is a
          diagram nobody scrolls to. */}
      <section>
        <h2>The map</h2>
        <FlowDiagram
          doors={map.entry_points}
          agents={map.agents}
          edges={map.edges}
          onPick={(agentId) => setFocus(agentId === focus ? null : agentId)}
        />
        {focus && (
          <div className="flow-focus" data-testid="flow-focus">
            <strong>{focus}</strong>
            <div className="auth-note">
              routes to {agentsById.get(focus)?.routes_to.join(', ') || 'nobody'}
              {' · may call '}
              {agentsById.get(focus)?.may_call.join(', ') || 'nothing'}
            </div>
            <Link to={`/agents/${encodeURIComponent(focus)}/profile`}>
              Read this profile as it really is
            </Link>
          </div>
        )}
      </section>

      <section>
        <h2>Gaps ({map.gaps.length})</h2>
        {map.edges.length > 0 && map.edges.every((edge) => !edge.declared) && (
          <p className="auth-note" data-testid="flow-no-conditions">
            All {map.edges.length} routing edges exist and none of them says <em>when</em> to
            take it. That is one situation, not {map.edges.length} separate problems: the
            agents know who their specialists are and nothing records why an ask should go to
            one rather than another.
          </p>
        )}
        {map.gaps.length === 0 ? (
          <p className="auth-note">
            Nothing is missing that this map can detect: every door names an agent, every
            specialist edge says when to take it, every Action has somebody who may call it
            and something to perform it, and every Workflow step names an Action that exists.
          </p>
        ) : (
          <ul className="flow-gaps" data-testid="flow-gaps">
            {map.gaps.map((gap, index) => (
              <li key={`${gap.kind}-${gap.subject}-${index}`}>
                <strong>{gap.subject}</strong>
                <div className="auth-note">{gap.says}</div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Doors in ({map.entry_points.length})</h2>
        {map.entry_points.length === 0 ? (
          <p className="auth-note">No outside door has been used, and none is declared.</p>
        ) : (
          <ul className="flow-doors" data-testid="flow-doors">
            {map.entry_points.map((door) => (
              <li key={`${door.source}-${door.chat_id}`}>
                <strong>{door.label}</strong> <span className="badge">{door.source}</span>
                {' → '}
                {door.reaches ? (
                  <code>{agentsById.get(door.reaches)?.name ?? door.reaches}</code>
                ) : (
                  <span className="auth-note">nothing yet</span>
                )}
                <div className="auth-note">
                  {door.declared_agent
                    ? `Declared ${door.declared_agent}`
                    : 'Not declared'}
                  {door.answered_by.length > 0 && ` · answered by ${door.answered_by.join(', ')}`}
                  {' · '}
                  <Link to="/entry-points">change</Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section>
        <h2>Routing ({map.edges.length})</h2>
        {map.edges.length === 0 ? (
          <p className="auth-note" data-testid="flow-no-edges">
            No agent on this install declares a specialist, so there is no routing to draw.
            Add one on an agent, say when to use it, then publish it into that agent's soul —
            the map fills in as you do, one agent at a time.
          </p>
        ) : (
          <ul className="flow-edges" data-testid="flow-edges">
            {map.edges.map((edge) => (
              <li key={`${edge.from}-${edge.to}`} className={edge.declared ? '' : 'flow-edge-silent'}>
                <code>{edge.from}</code> → <code>{edge.to}</code>
                <div className="auth-note">
                  {edge.when ? `When: ${edge.when}` : 'No condition said — the agent decides from the description alone.'}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {canEditRouting && map.edges.length > 0 && (
        <section>
          <h2>Say when to take each route</h2>
          <p className="auth-note">
            Saving records what you meant. Publishing writes it into that one agent's
            SOUL.md — a live prompt change, one agent at a time, never a sweep.
          </p>
          {[...new Set(map.edges.map((edge) => edge.from))].map((parent) => (
            <RoutingEditor
              key={parent}
              parent={parent}
              edges={map.edges.filter((edge) => edge.from === parent)}
              targets={targets}
              onSaved={() => setReloads((n) => n + 1)}
            />
          ))}
        </section>
      )}

      <section>
        <h2>What can be done ({map.actions.length})</h2>
        <table className="settings-table" data-testid="flow-actions">
          <thead>
            <tr><th>Action</th><th>Touches</th><th>Who may call it</th></tr>
          </thead>
          <tbody>
            {map.actions.map((action) => (
              <tr key={action.id}>
                <td>
                  <code>{action.id}</code>
                  {action.is_blocked && (
                    <> <span className="badge badge-danger">Blocked</span></>
                  )}
                  {action.is_blocked && action.blocked_reason && (
                    <div className="auth-note">{action.blocked_reason}</div>
                  )}
                </td>
                <td className="auth-note">{action.touches ?? 'nothing — no implementation'}</td>
                <td className="auth-note">
                  {action.callers.length === 0
                    ? 'nobody'
                    : action.callers.length === map.agents.length
                      ? `every agent (${action.callers.length})`
                      : action.callers.join(', ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="auth-note">
          Block or release an Action in <Link to="/settings/actions">Settings → Actions</Link>.
        </p>
      </section>

      {map.workflows.length > 0 && (
        <section>
          <h2>Workflows ({map.workflows.length})</h2>
          {map.workflows.map((workflow) => (
            <div key={workflow.id} className="flow-workflow">
              <strong>{workflow.id}</strong>
              {workflow.request_kind && <span className="auth-note"> · {workflow.request_kind}</span>}
              <ol>
                {workflow.steps.map((step) => (
                  <li key={step.position}>
                    <code>{step.action_id ?? '(no action)'}</code>
                    {step.needs_confirmation && <> <span className="badge badge-warning">needs you</span></>}
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </section>
      )}

      <p className="auth-note" data-testid="flow-counts">
        {map.counts.agents} agents · {map.counts.edges} routing edges · {map.counts.actions} actions ·{' '}
        {map.counts.workflows} workflows · {map.counts.entry_points} doors.
      </p>
    </>
  );
}
