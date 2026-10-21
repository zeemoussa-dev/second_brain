import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router';
import { refusalText } from '../features/auth/SignInScreen';
import { fetchAgentList, type AgentSummary } from '../features/agents-map/agentsApiClient';
import {
  fetchAgentTokens,
  mintAgentToken,
  revokeAgentToken,
  type AgentTokenRow,
  type MintedAgentToken,
} from '../features/settings/agentTokensApiClient';

/** REQ-SB-103 / ADR-062 — the keys Hermes workers use to reach this app.
 *
 * **A key is for one agent and is not a person.** It lets a worker read
 * what this install knows, call Actions through the gate and step
 * through Workflows. It cannot author anything, cannot confirm an
 * Action call, and cannot approve anything on anybody's behalf: when a
 * worker relays a person's answer it names the chat it came from and
 * the app decides whose chat that is, on the Entry points screen.
 *
 * **The key is shown once, here, and never again.** Only its
 * fingerprint is stored. The screen therefore holds the new key in
 * front of the operator until they dismiss it, and says plainly that
 * leaving the page loses it.
 */
export function SettingsAgentAccessPage() {
  const [rows, setRows] = useState<AgentTokenRow[] | null>(null);
  const [agents, setAgents] = useState<AgentSummary[] | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [agentId, setAgentId] = useState('');
  const [label, setLabel] = useState('');
  const [minted, setMinted] = useState<MintedAgentToken | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setRows(await fetchAgentTokens());
      setFailure(null);
    } catch (error) {
      setFailure(refusalText(error));
    }
  }, []);

  useEffect(() => {
    void load();
    fetchAgentList().then(setAgents, () => setAgents(null));
  }, [load]);

  async function mint() {
    setBusy(true);
    setFailure(null);
    try {
      setMinted(await mintAgentToken(agentId.trim(), label.trim()));
      setLabel('');
      await load();
    } catch (error) {
      setFailure(refusalText(error));
    } finally {
      setBusy(false);
    }
  }

  async function revoke(row: AgentTokenRow) {
    setBusy(true);
    setFailure(null);
    try {
      await revokeAgentToken(row.token_sha256);
      await load();
    } catch (error) {
      setFailure(refusalText(error));
    } finally {
      setBusy(false);
    }
  }

  if (failure && !rows) {
    return <><h1>Agent access</h1><p className="auth-refusal" role="alert">{failure}</p></>;
  }
  if (!rows) return <><h1>Agent access</h1><p>Reading the issued keys…</p></>;

  return (
    <>
      <p><Link to="/admin">← Admin Center</Link></p>
      <h1>Agent access</h1>
      <p className="text-muted">
        The keys your Hermes workers use to reach this app. Each one belongs to a single agent.
        A worker holding one can read what this install knows, call Actions through the gate and
        step through Workflows — it cannot author Actions or Workflows, cannot confirm an Action
        call, and cannot approve anything as a person. When it relays somebody's answer it names
        the chat that answer came from, and{' '}
        <Link to="/entry-points">whose chat that is</Link> is yours to declare.
      </p>

      {failure && <p className="auth-refusal" role="alert">{failure}</p>}

      {minted && (
        <div className="auth-note" data-testid="agent-token-minted" style={{ borderLeft: '3px solid var(--accent, #c80)', paddingLeft: '12px' }}>
          <p><strong>Copy this now — it will not be shown again.</strong></p>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', margin: '8px 0' }}>
            <code>{minted.token}</code>
          </pre>
          <p>
            Put it in that worker's environment as <code>SECOND_BRAIN_AGENT_TOKEN</code>. Only its
            fingerprint is stored here, so if it is lost the fix is to revoke this key and mint
            another.
          </p>
          <button type="button" className="btn" onClick={() => setMinted(null)}>
            I have copied it
          </button>
        </div>
      )}

      <h2>Issue a key</h2>
      <div className="entry-point-declare">
        {/* A picker only where there is something to pick. `null` is
            "the roster could not be read" and `[]` is "this install has
            no agents yet" — different facts, same consequence here, and
            an empty select would leave no way to issue a key at all. A
            key is routinely minted before its agent is deployed, which
            is exactly when both of these are true. */}
        {agents !== null && agents.length > 0 ? (
          <select
            aria-label="Agent this key is for"
            value={agentId}
            onChange={(event) => setAgentId(event.target.value)}
          >
            <option value="">choose an agent…</option>
            {/* Deduplicated: this install's roster really does list
                `default` twice, and two identical options are noise in
                a picker rather than information. The duplicate itself
                is the roster's to answer for, not this screen's. */}
            {Array.from(new Set(agents.map((agent) => agent.id))).map((id) => (
              <option key={id} value={id}>{id}</option>
            ))}
          </select>
        ) : (
          // The roster could not be read — which is normal while Hermes
          // is down, and no reason to block issuing a key. A key is
          // routinely minted before its agent is deployed.
          <input
            aria-label="Agent this key is for"
            placeholder="agent id"
            value={agentId}
            onChange={(event) => setAgentId(event.target.value)}
          />
        )}
        <input
          aria-label="What this key is for"
          placeholder="what this key is for — e.g. the WhatsApp worker"
          value={label}
          onChange={(event) => setLabel(event.target.value)}
        />
        <button type="button" disabled={busy || !agentId.trim()} onClick={() => void mint()}>
          Issue
        </button>
      </div>

      <h2>Issued</h2>
      {rows.length === 0 ? (
        <p className="auth-note" data-testid="agent-tokens-empty">
          No key has been issued. Until one is, a Hermes worker reaching this app is refused —
          it has no way to say which agent it is.
        </p>
      ) : (
        <table className="settings-table" data-testid="agent-tokens-table">
          <thead>
            <tr>
              <th>Agent</th>
              <th>What it is for</th>
              <th>Used</th>
              <th>State</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.token_sha256} data-testid={`agent-token-${row.token_sha256}`}>
                <td>
                  <strong>{row.agent_id}</strong>
                  <div className="auth-note">
                    issued {row.created_at.slice(0, 10)}
                    {row.created_by ? ` by ${row.created_by}` : ''}
                  </div>
                </td>
                <td>{row.label || <span className="auth-note">not said</span>}</td>
                <td>
                  {row.has_ever_been_used ? (
                    row.last_seen_at?.slice(0, 16).replace('T', ' ')
                  ) : (
                    <span className="auth-note">never — check it reached the worker</span>
                  )}
                </td>
                <td>
                  {row.is_revoked ? (
                    <>
                      <span className="badge badge-danger">Revoked</span>
                      <div className="auth-note">{row.revoked_at?.slice(0, 10)}</div>
                    </>
                  ) : (
                    <span className="badge badge-success">Active</span>
                  )}
                </td>
                <td>
                  {!row.is_revoked && (
                    <button
                      type="button"
                      className="btn btn-danger"
                      disabled={busy}
                      onClick={() => void revoke(row)}
                    >
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="auth-note">
        A revoked key stays on this list, dated. After a key has leaked, “was it revoked, and
        when” is the question that matters, and a row that vanished would answer it for nobody.
      </p>
    </>
  );
}
