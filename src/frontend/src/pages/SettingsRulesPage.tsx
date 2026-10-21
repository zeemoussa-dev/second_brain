import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router';
import { apiFetch } from '../api/client';
import { refusalText } from '../features/auth/SignInScreen';

interface Rule {
  id: string;
  name: string;
  action_id: string;
  caller_agent_id: string;
  input_name: string;
  kind: 'refuse_if' | 'refuse_unless';
  pattern: string;
  effect: 'refuse' | 'needs_confirmation';
  reason: string;
  enabled: boolean;
}

const BLANK: Rule = {
  id: '', name: '', action_id: '*', caller_agent_id: '*', input_name: '',
  kind: 'refuse_if', pattern: '', effect: 'refuse', reason: '', enabled: true,
};

/** REQ-SB-102 — rules evaluated when an Action is called, against the
 * inputs it was called with.
 *
 * **The two kinds are explained in the words of real examples**, not as
 * `refuse_if` / `refuse_unless`. The difference between them only shows
 * up when the named input is missing, which is precisely the case an
 * operator will not think about while typing — and getting it wrong
 * means a rule that reads like "never" and is not one.
 *
 * **Order is meaning and the page says so.** The gate stops at the
 * first rule that refuses, so the list is ordered, movable, and never
 * sorted for tidiness.
 */
export function SettingsRulesPage() {
  const [rules, setRules] = useState<Rule[] | null>(null);
  const [failure, setFailure] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setRules(await apiFetch<Rule[]>('/actions/rules'));
    } catch (error) {
      setFailure(refusalText(error));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function save(next: Rule[]) {
    setFailure(null);
    setNote(null);
    setBusy(true);
    try {
      setRules(await apiFetch<Rule[]>('/actions/rules', {
        method: 'PUT', body: JSON.stringify(next),
      }));
      setNote('Saved. These apply to the next call.');
    } catch (error) {
      // The backend compiles every pattern before writing anything, so
      // a refusal here means NOTHING was saved -- shown as the
      // backend's own sentence, which names the rule and the error.
      setFailure(refusalText(error));
    } finally {
      setBusy(false);
    }
  }

  function patch(index: number, change: Partial<Rule>) {
    setRules((current) =>
      (current ?? []).map((rule, i) => (i === index ? { ...rule, ...change } : rule)),
    );
  }

  function move(index: number, by: number) {
    setRules((current) => {
      const next = [...(current ?? [])];
      const target = index + by;
      if (target < 0 || target >= next.length) return next;
      [next[index], next[target]] = [next[target], next[index]];
      return next;
    });
  }

  if (!rules) {
    return <><h1>Rules</h1>{failure ? <p className="auth-refusal" role="alert">{failure}</p> : <p>Loading…</p>}</>;
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Rules</h1>
      <p className="text-muted">
        Checked every time an Action is called, against what it was asked to do. A{' '}
        <Link to="/settings/actions">block</Link> turns an Action off for everyone; a rule
        lets it run a hundred times and stops the hundred-and-first.
      </p>

      <div className="auth-card rules-explainer">
        <h2>The two kinds, and why the difference matters</h2>
        <p className="auth-note">
          <strong>Only allow when…</strong> — “only ever mail an address ending
          <code> @core42.ai</code>”. If a call arrives with <em>no</em> address at all, it is
          <strong> refused</strong>: nothing proves it was inside the company, and a rule
          that waved through the one call it could not check would not be a “never”.
        </p>
        <p className="auth-note">
          <strong>Never allow when…</strong> — “never write to <code>C:/Windows</code>”. If a
          call arrives with no path at all, it is <strong>allowed</strong>: there is nothing
          matching the forbidden thing, and refusing every call it could not check would stop
          Actions that have no such input.
        </p>
        <p className="auth-note">
          Rules are checked <strong>in order</strong> and the first refusal wins, so what is
          above what decides which reason a blocked call reports.
        </p>
      </div>

      {failure && <p className="auth-refusal" role="alert" data-testid="rules-failure">{failure}</p>}
      {note && <p className="profile-done" role="status">{note}</p>}

      {rules.length === 0 && (
        <p className="auth-note" data-testid="rules-empty">
          No rules. Every call is judged only by who may call the Action and whether its
          inputs are well formed.
        </p>
      )}

      {rules.map((rule, index) => (
        <div className="auth-card rule-card" key={rule.id || index} data-testid={`rule-${index}`}>
          <div className="rule-head">
            <input
              aria-label="Rule name"
              className="rule-name"
              placeholder="what this rule is for"
              value={rule.name}
              onChange={(event) => patch(index, { name: event.target.value })}
            />
            <label className="rule-enabled">
              <input
                type="checkbox"
                checked={rule.enabled}
                onChange={(event) => patch(index, { enabled: event.target.checked })}
              />{' '}
              on
            </label>
            <button type="button" onClick={() => move(index, -1)} disabled={index === 0}>↑</button>
            <button type="button" onClick={() => move(index, 1)} disabled={index === rules.length - 1}>↓</button>
            <button
              type="button"
              className="btn-danger"
              onClick={() => setRules(rules.filter((_, i) => i !== index))}
            >
              Remove
            </button>
          </div>

          <div className="rule-grid">
            <label className="auth-field">
              <span>When this Action is called</span>
              <input
                value={rule.action_id}
                placeholder="* for any"
                onChange={(event) => patch(index, { action_id: event.target.value || '*' })}
              />
            </label>
            <label className="auth-field">
              <span>By this agent</span>
              <input
                value={rule.caller_agent_id}
                placeholder="* for any"
                onChange={(event) => patch(index, { caller_agent_id: event.target.value || '*' })}
              />
            </label>
            <label className="auth-field">
              <span>Look at this input</span>
              <input
                value={rule.input_name}
                placeholder="to, path, name…"
                onChange={(event) => patch(index, { input_name: event.target.value })}
              />
            </label>
            <label className="auth-field">
              <span>Rule</span>
              <select
                value={rule.kind}
                onChange={(event) => patch(index, { kind: event.target.value as Rule['kind'] })}
              >
                <option value="refuse_unless">Only allow when it matches</option>
                <option value="refuse_if">Never allow when it matches</option>
              </select>
            </label>
            <label className="auth-field">
              <span>This pattern</span>
              <input
                className="rule-pattern"
                value={rule.pattern}
                placeholder="@core42[.]ai$"
                onChange={(event) => patch(index, { pattern: event.target.value })}
              />
            </label>
            <label className="auth-field">
              <span>Then</span>
              <select
                value={rule.effect}
                onChange={(event) => patch(index, { effect: event.target.value as Rule['effect'] })}
              >
                <option value="refuse">Refuse the call</option>
                <option value="needs_confirmation">Ask me first</option>
              </select>
            </label>
          </div>

          <label className="auth-field">
            <span>Why — the agent is told this</span>
            <input
              value={rule.reason}
              placeholder="so a refused agent can tell you something useful"
              onChange={(event) => patch(index, { reason: event.target.value })}
            />
          </label>

          {rule.kind === 'refuse_unless' && (
            <p className="auth-note">
              A call with no <code>{rule.input_name || 'input'}</code> at all will be refused
              by this rule.
            </p>
          )}
        </div>
      ))}

      <div className="rules-actions">
        <button
          type="button"
          onClick={() => setRules([...rules, { ...BLANK, id: `rule-${rules.length + 1}` }])}
        >
          Add a rule
        </button>
        <button
          type="button"
          className="auth-primary"
          data-testid="rules-save"
          disabled={busy}
          onClick={() => void save(rules)}
        >
          {busy ? 'Saving…' : 'Save all rules'}
        </button>
      </div>
      <p className="auth-note">
        Patterns are checked when you save: if one is not valid the save is refused in full
        and nothing changes, rather than leaving a rule that stops nothing.
      </p>
    </>
  );
}
