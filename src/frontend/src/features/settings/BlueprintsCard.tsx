import { useEffect, useState } from 'react';
import {
  fetchBlueprints, preflightBlueprint, installBlueprint,
  type Blueprint, type BlueprintPreflight, type BlueprintInstallResult,
} from './blueprintsApiClient';

// Settings > Blueprints. A Blueprint is a RECIPE for a Section -- its
// identity, the Agents in it, and each Agent's Skills -- so a fresh install
// can pull one and have that Section running.
//
// Preflight is always shown BEFORE install is offered. It creates nothing, so
// the operator sees exactly what would happen (and what would stop it) rather
// than finding out afterwards.

function ProblemList({ problems }: { problems: string[] }) {
  return (
    <ul className="blueprint-problems">
      {problems.map((problem) => <li key={problem}>{problem}</li>)}
    </ul>
  );
}

function PreflightDetail({ check }: { check: BlueprintPreflight }) {
  return (
    <div className="blueprint-preflight">
      {check.ok
        ? <p className="text-muted">Ready to install.</p>
        : (<><p><strong>Cannot install:</strong></p><ProblemList problems={check.problems} /></>)}

      <dl className="blueprint-facts">
        <dt>Skills</dt><dd>{check.skills.join(', ') || '—'}</dd>
        <dt>Templates required</dt><dd>{check.templates.join(', ') || '—'}</dd>
        <dt>Peers of Primary</dt>
        <dd>{check.peers.join(', ') || '—'}</dd>
      </dl>

      {check.unchecked_skills.length > 0 && (
        // A partial check that reads as a clean one is worse than no check.
        <p className="text-muted">
          Not checked against any Template ({check.unchecked_skills.join(', ')}) — these Skills
          declare no <code>writes:</code>, so the Template check could not cover them.
        </p>
      )}

      {(check.already.section || check.already.agents.length > 0) && (
        <p className="text-muted">
          Already here: {check.already.section ? 'the Section' : ''}
          {check.already.section && check.already.agents.length > 0 ? ', ' : ''}
          {check.already.agents.join(', ')}. Installing tops it up rather than duplicating.
        </p>
      )}
    </div>
  );
}

export function BlueprintsCard() {
  const [blueprints, setBlueprints] = useState<Blueprint[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [check, setCheck] = useState<BlueprintPreflight | null>(null);
  const [busy, setBusy] = useState(false);
  const [sectionId, setSectionId] = useState<string>('');
  const [result, setResult] = useState<BlueprintInstallResult | null>(null);

  useEffect(() => {
    fetchBlueprints().then(setBlueprints).catch((e) => setError(String(e)));
  }, []);

  async function open(id: string, section?: string) {
    setOpenId(id);
    setCheck(null);
    setResult(null);
    setError(null);
    try {
      setCheck(await preflightBlueprint(id, section || undefined));
    } catch (e) {
      setError(String(e));
    }
  }

  async function install(id: string) {
    setBusy(true);
    setError(null);
    try {
      setResult(await installBlueprint(id, sectionId || undefined));
      setCheck(await preflightBlueprint(id, sectionId || undefined));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }

  if (error && !blueprints) return <p className="error-text">{error}</p>;
  if (!blueprints) return <p className="text-muted">Loading blueprints…</p>;
  if (blueprints.length === 0) return <p className="text-muted">No blueprints ship with this install.</p>;

  return (
    <div className="card">
      {blueprints.map((blueprint) => (
        <div key={blueprint.id} className="blueprint-row">
          <div className="blueprint-head">
            <span className="material-symbols-outlined" aria-hidden="true">
              {blueprint.suggested_section_icon || 'dashboard_customize'}
            </span>
            <div>
              <strong>{blueprint.name}</strong> <span className="text-muted">v{blueprint.version}</span>
              <p className="text-muted">{blueprint.description}</p>
            </div>
            <button type="button" className="btn" onClick={() => open(blueprint.id)}>
              {openId === blueprint.id ? 'Refresh check' : 'Check'}
            </button>
          </div>

          {blueprint.error && (
            <p className="error-text">This blueprint did not parse: {blueprint.error}</p>
          )}

          <ul className="blueprint-agents">
            {blueprint.agents.map((agent) => (
              <li key={agent.id}>
                <span className="material-symbols-outlined" aria-hidden="true">{agent.icon || 'smart_toy'}</span>
                <strong>{agent.name}</strong> <span className="text-muted">{agent.type}</span>
                {agent.peer && <span className="badge" title="Primary relays to this agent">peer</span>}
                <span className="text-muted"> — {agent.skill_ids.join(', ') || 'no skills'}</span>
              </li>
            ))}
          </ul>

          {openId === blueprint.id && check && (
            <>
              <PreflightDetail check={check} />

              <label className="blueprint-section-picker">
                Install into section
                <select
                  value={sectionId}
                  onChange={(e) => { setSectionId(e.target.value); open(blueprint.id, e.target.value); }}
                >
                  {/* The Blueprint suggests; the operator decides (BUG-046). */}
                  <option value="">New section — “{check.suggested_section}”</option>
                  {check.available_sections.map((s) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </label>

              <button
                type="button"
                className="btn btn-primary"
                disabled={!check.ok || busy}
                onClick={() => install(blueprint.id)}
              >
                {busy ? 'Installing…' : 'Install'}
              </button>
            </>
          )}

          {openId === blueprint.id && result && (
            <div className="blueprint-result">
              <p><strong>Installed into section “{result.section_id}”.</strong></p>
              <ul>
                {Object.entries(result.agents).map(([id, state]) => <li key={id}>{id}: {state}</li>)}
              </ul>
              {Object.keys(result.peers).length > 0 && (
                <p className="text-muted">
                  Primary routing: {Object.entries(result.peers).map(([id, s]) => `${id} — ${s}`).join('; ')}
                </p>
              )}
              {result.primary_session_reset_required && (
                // Hermes injects a session's prompt once and never re-reads it,
                // so a conversation already in progress cannot see the new peers.
                <p className="error-text">
                  Start a new conversation with your Primary agent for this to take effect —
                  a running session will not pick up the new peers.
                </p>
              )}
            </div>
          )}

          {openId === blueprint.id && error && <p className="error-text">{error}</p>}
        </div>
      ))}
    </div>
  );
}
