import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router';
import { useAuth } from '../features/auth/AuthGate';
import { refusalText } from '../features/auth/SignInScreen';
import { fetchEntryPoints, saveEntryPoints } from '../features/hermes-ops/client';
import type { EntryPoint, EntryPointsView } from '../features/hermes-ops/client';

const STATUS_LABELS: Record<EntryPoint['status'], string> = {
  drifted: 'Drifted',
  observed_only: 'Not declared',
  declared_only: 'Never used',
  agrees: 'Agrees',
};

const STATUS_MEANING: Record<EntryPoint['status'], string> = {
  drifted: 'You said one agent should answer this; a different one did.',
  observed_only: 'Real traffic arrived here and nobody wrote down which agent should take it.',
  declared_only: 'Written down, but no session has ever come through it.',
  agrees: 'The agent you named is the one answering.',
};

const STATUS_BADGE: Record<EntryPoint['status'], string> = {
  drifted: 'badge badge-danger',
  observed_only: 'badge badge-warning',
  declared_only: 'badge',
  agrees: 'badge badge-success',
};

/** REQ-SB-102 — the outside doors into this install, and which agent
 * answers each.
 *
 * **Observed first, declared second.** Hermes has no configuration to
 * read for this, so the rows come from real traffic: every session
 * carries its source, the profile that answered, and the chat it came
 * from. What the operator declares sits BESIDE that, never instead of
 * it — a hand-written map of numbers to agents is a second truth that
 * nobody checks, and the day Hermes is rewired it becomes a confident
 * lie.
 *
 * **Nothing is auto-corrected, and the page says so.** When a
 * declaration and the traffic disagree, the app cannot know which side
 * is right: the declaration may be the intent and the traffic the bug,
 * or the reverse. Both are shown and the disagreement is named.
 */
export function EntryPointsPage() {
  const { may } = useAuth();
  const canDeclare = may('manage_hermes');
  const [view, setView] = useState<EntryPointsView | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setView(await fetchEntryPoints());
    } catch (error) {
      setFailure(refusalText(error));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const keyOf = (row: EntryPoint) => `${row.source}::${row.chat_id}`;

  async function declare(row: EntryPoint) {
    if (!view) return;
    const agentId = (draft[keyOf(row)] ?? row.agent_id ?? '').trim();
    // The whole declared set is sent: it is small, and the operator is
    // editing a map, so saving the map they are looking at is the
    // honest operation.
    const next = view.entry_points
      .map((entry) => ({
        label: entry.label ?? entry.observed?.chat_name ?? entry.chat_id,
        source: entry.source,
        chat_id: entry.chat_id,
        agent_id: keyOf(entry) === keyOf(row) ? agentId : entry.agent_id,
      }))
      .filter((entry) => entry.agent_id);
    setFailure(null);
    setBusy(true);
    try {
      setView(await saveEntryPoints(next));
    } catch (error) {
      setFailure(refusalText(error));
    } finally {
      setBusy(false);
    }
  }

  if (failure && !view) {
    return <><h1>Entry points</h1><p className="auth-refusal" role="alert">{failure}</p></>;
  }
  if (!view) return <><h1>Entry points</h1><p>Reading the doors…</p></>;

  const attention = view.summary.needs_attention.length;

  return (
    <>
      <h1>Entry points</h1>
      <p className="text-muted">
        The outside doors into this install, and which agent answers each one. The rows come
        from real traffic — what you declare is checked against it rather than believed.
      </p>

      {!view.reachable && (
        <p className="auth-refusal" role="alert" data-testid="entry-points-unreachable">
          Hermes could not be reached, so nothing here has been checked against real traffic.
          Your declarations are shown as written; whether they are true is unknown right now.
          {view.error ? ` ${view.error}` : ''}
        </p>
      )}
      {failure && <p className="auth-refusal" role="alert">{failure}</p>}

      {attention > 0 && (
        <p className="auth-note" data-testid="entry-points-attention">
          <strong>{attention}</strong> {attention === 1 ? 'door needs' : 'doors need'} a look —
          either nobody declared them, or what answered is not what you said would.
        </p>
      )}

      {view.entry_points.length === 0 ? (
        <p className="auth-note" data-testid="entry-points-empty">
          No outside door has been used, and none is declared. Scheduled jobs and this app's
          own calls are deliberately not counted — they are not doors anyone comes in through.
        </p>
      ) : (
        <table className="settings-table" data-testid="entry-points-table">
          <thead>
            <tr>
              <th>Door</th>
              <th>Should reach</th>
              <th>Actually answered</th>
              <th>State</th>
            </tr>
          </thead>
          <tbody>
            {view.entry_points.map((row) => (
              <tr key={keyOf(row)} data-testid={`entry-point-${row.chat_id}`}>
                <td>
                  <strong>{row.observed?.chat_name || row.label || row.chat_id}</strong>
                  <div className="auth-note">
                    {row.source}
                    {row.observed?.chat_type ? ` · ${row.observed.chat_type}` : ''} · {row.chat_id}
                  </div>
                  {row.observed && (
                    <div className="auth-note">
                      {row.observed.session_count} session
                      {row.observed.session_count === 1 ? '' : 's'}
                      {row.observed.last_session_id && (
                        <>
                          {' · '}
                          <Link to={`/agent-activity/${encodeURIComponent(row.observed.last_session_id)}`}>
                            read the last one
                          </Link>
                        </>
                      )}
                    </div>
                  )}
                </td>
                <td>
                  {canDeclare ? (
                    <div className="entry-point-declare">
                      <input
                        aria-label={`Agent for ${row.chat_id}`}
                        placeholder="agent id"
                        value={draft[keyOf(row)] ?? row.agent_id ?? ''}
                        onChange={(event) =>
                          setDraft((d) => ({ ...d, [keyOf(row)]: event.target.value }))
                        }
                      />
                      <button type="button" disabled={busy} onClick={() => void declare(row)}>
                        Save
                      </button>
                    </div>
                  ) : (
                    row.agent_id ?? <span className="auth-note">not declared</span>
                  )}
                </td>
                <td>
                  {row.answered_by.length === 0 ? (
                    <span className="auth-note">never</span>
                  ) : (
                    row.answered_by.join(', ')
                  )}
                </td>
                <td>
                  <span className={STATUS_BADGE[row.status]}>{STATUS_LABELS[row.status]}</span>
                  <div className="auth-note">{STATUS_MEANING[row.status]}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {view.scanned && (
        <p className="auth-note" data-testid="entry-points-scanned">
          Read from the {view.scanned.sessions_read} most recent sessions that came from
          outside. {view.scanned.internal_sources_excluded.join(', ')} are excluded — they are
          this machine talking to itself, not a door.
        </p>
      )}
      {!canDeclare && (
        <p className="auth-note">
          Declaring which agent a door should reach needs an Admin.
        </p>
      )}
    </>
  );
}
