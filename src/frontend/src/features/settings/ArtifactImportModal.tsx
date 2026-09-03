import { useState } from 'react';
import { Modal } from './Modal';
import {
  previewImport, commitImport, applyPrimaryRouting, CREATE_NEW_SECTION_PREFIX,
  type ImportPreviewResult, type ImportOutcome,
} from './artifactsApiClient';
import { extractErrorDetail } from './artifactFlowUtils';

function decisionKey(kind: string, id: string): string {
  return `${kind}:${id}`;
}

// UI-local sentinel for "create a new section" -- distinct from the
// backend's own CREATE_NEW_SECTION_PREFIX string (which needs a real
// name appended); this just marks the <select> state so the name input
// renders, composed into the real prefixed string only when building the
// commit payload.
const CREATE_NEW_SECTION_CHOICE = '__new__';

// Import, as a popup (operator, 2026-09-01: "The Confirmation should be a
// popup not in the header of the Page") — upload, preview, per-artifact
// conflict resolution, commit, and the outcome report all now live inside
// ONE modal rather than growing inline down the page. Fully self-contained
// (owns its own file/preview/decisions/outcome state) so the parent page
// only needs to render <ArtifactImportModal onClose={...} /> and forget it.
interface ArtifactImportModalProps {
  onClose: () => void;
}

export function ArtifactImportModal({ onClose }: ArtifactImportModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResult | null>(null);
  const [decisions, setDecisions] = useState<Record<string, 'overwrite' | 'skip' | 'keep_both'>>({});
  const [skillTargetProfiles, setSkillTargetProfiles] = useState<Record<string, string[]>>({});
  // Section placement for each bundled Agent -- omitted entirely from the
  // commit payload unless the operator actively picks something (matches
  // the backend's own "no decision = keep the existing Data Gatherer
  // fallback, never blocks the import" contract exactly).
  const [sectionChoice, setSectionChoice] = useState<Record<string, string>>({});
  const [newSectionName, setNewSectionName] = useState<Record<string, string>>({});
  const [outcomes, setOutcomes] = useState<ImportOutcome[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [routingStatus, setRoutingStatus] = useState<Record<string, string>>({});
  const [routingLoading, setRoutingLoading] = useState<string | null>(null);

  async function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    event.target.value = ''; // Allows re-selecting the SAME file a second time -- otherwise onChange never fires again for an identical path.
    if (!selected) {
      return;
    }
    setFile(selected);
    setError(null);
    setPreview(null);
    setOutcomes(null);
    setDecisions({});
    setSkillTargetProfiles({});
    setSectionChoice({});
    setNewSectionName({});
    setRoutingStatus({});
    try {
      const result = await previewImport(selected);
      setPreview(result);
      // "default" pre-checked for every bundled Skill -- mirrors the
      // backend's own documented default (skill_target_profiles.get(id)
      // or ["default"]).
      const skillDefaults: Record<string, string[]> = {};
      for (const artifact of result.artifacts) {
        if (artifact.kind === 'skill') {
          skillDefaults[artifact.id] = ['default'];
        }
      }
      setSkillTargetProfiles(skillDefaults);
    } catch (previewError) {
      setError(extractErrorDetail(previewError));
    }
  }

  function setDecision(kind: string, id: string, decision: 'overwrite' | 'skip' | 'keep_both') {
    setDecisions((previous) => ({ ...previous, [decisionKey(kind, id)]: decision }));
  }

  function toggleSkillTargetProfile(id: string, profile: string) {
    setSkillTargetProfiles((previous) => {
      const current = new Set(previous[id] ?? []);
      if (current.has(profile)) {
        current.delete(profile);
      } else {
        current.add(profile);
      }
      return { ...previous, [id]: Array.from(current) };
    });
  }

  const allConflictsResolved = preview
    ? preview.artifacts.filter((artifact) => artifact.conflicts).every((artifact) => Boolean(decisions[decisionKey(artifact.kind, artifact.id)]))
    : false;

  // Only an agent id whose operator actually picked something makes it
  // into the payload -- an untouched picker means "keep the existing
  // Data Gatherer fallback", never a value the backend has to guess at.
  function buildAgentSectionDecisions(): Record<string, string> {
    const result: Record<string, string> = {};
    for (const [agentId, choice] of Object.entries(sectionChoice)) {
      if (!choice) continue;
      if (choice === CREATE_NEW_SECTION_CHOICE) {
        const name = (newSectionName[agentId] ?? '').trim();
        if (name) result[agentId] = `${CREATE_NEW_SECTION_PREFIX}${name}`;
      } else {
        result[agentId] = choice;
      }
    }
    return result;
  }

  async function handleCommit() {
    if (!file) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await commitImport(file, decisions, skillTargetProfiles, buildAgentSectionDecisions());
      setOutcomes(result);
    } catch (commitError) {
      setError(extractErrorDetail(commitError));
    } finally {
      setLoading(false);
    }
  }

  // Never automatic -- an explicit, per-agent operator action, same
  // "never silent" posture as the conflict decisions above. Re-clicking
  // after a successful apply is a safe no-op (backend's own idempotency
  // guard, keyed by a marker in the target's real Primary SOUL.md).
  async function handleApplyPrimaryRouting(agentId: string, snippet: string) {
    setRoutingLoading(agentId);
    try {
      const result = await applyPrimaryRouting(agentId, snippet);
      setRoutingStatus((previous) => ({ ...previous, [agentId]: result.detail }));
    } catch (applyError) {
      setRoutingStatus((previous) => ({ ...previous, [agentId]: extractErrorDetail(applyError) }));
    } finally {
      setRoutingLoading(null);
    }
  }

  const footer = outcomes ? (
    <button type="button" className="btn btn-primary" data-testid="import-done" onClick={onClose}>
      Done
    </button>
  ) : preview ? (
    <>
      <button type="button" className="btn" data-testid="import-cancel" onClick={onClose}>
        Cancel
      </button>
      <button
        type="button"
        className="btn btn-primary"
        data-testid="import-commit"
        disabled={loading || !allConflictsResolved}
        onClick={handleCommit}
      >
        {loading ? 'Importing…' : 'Commit import'}
      </button>
    </>
  ) : (
    <button type="button" className="btn" data-testid="import-cancel" onClick={onClose}>
      Cancel
    </button>
  );

  return (
    <Modal
      title="Import"
      description="Upload a real .sbf bundle to preview its contents and resolve any conflicts before deploying."
      onClose={onClose}
      footer={footer}
    >
      {!preview && !outcomes && (
        <input type="file" accept=".sbf" data-testid="import-file-input" onChange={handleFileChange} />
      )}

      {error && (
        <p data-role="import-error" style={{ color: 'var(--color-danger)', marginTop: 'var(--space-3)' }}>
          {error}
        </p>
      )}

      {preview && !outcomes && (
        <div data-role="import-contents-preview">
          <h3>Bundle contents</h3>
          <div className="item-list">
            {preview.artifacts.map((artifact) => {
              const decision = decisions[decisionKey(artifact.kind, artifact.id)];
              return (
                <div className="item-row" key={`${artifact.kind}:${artifact.id}`}>
                  <div className="item-row-main">
                    <span className="item-row-title">{artifact.id}</span>
                    <span className="item-row-meta">
                      {artifact.kind}
                      {' · '}
                      {artifact.conflicts ? 'conflicts with an existing artifact' : 'no conflict'}
                    </span>
                    {artifact.kind === 'skill' && (
                      <span className="item-row-meta">
                        Deploy to:
                        {preview.available_profiles.map((profile) => (
                          <label key={profile} style={{ marginLeft: 'var(--space-2)' }}>
                            <input
                              type="checkbox"
                              data-testid={`skill-target-profile-${artifact.id}-${profile}`}
                              checked={(skillTargetProfiles[artifact.id] ?? []).includes(profile)}
                              onChange={() => toggleSkillTargetProfile(artifact.id, profile)}
                            />
                            {' '}{profile}
                          </label>
                        ))}
                      </span>
                    )}
                    {artifact.kind === 'agent' && (
                      <span className="item-row-meta" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                        Section:
                        <select
                          data-testid={`agent-section-choice-${artifact.id}`}
                          value={sectionChoice[artifact.id] ?? ''}
                          onChange={(event) =>
                            setSectionChoice((previous) => ({ ...previous, [artifact.id]: event.target.value }))
                          }
                        >
                          <option value="">Default (Data Gatherer)</option>
                          {preview.available_sections.map((section) => (
                            <option key={section.id} value={section.id}>{section.name}</option>
                          ))}
                          <option value={CREATE_NEW_SECTION_CHOICE}>+ Create new section…</option>
                        </select>
                        {sectionChoice[artifact.id] === CREATE_NEW_SECTION_CHOICE && (
                          <input
                            type="text"
                            placeholder="New section name"
                            data-testid={`agent-new-section-name-${artifact.id}`}
                            value={newSectionName[artifact.id] ?? ''}
                            onChange={(event) =>
                              setNewSectionName((previous) => ({ ...previous, [artifact.id]: event.target.value }))
                            }
                          />
                        )}
                      </span>
                    )}
                  </div>
                  {artifact.conflicts && (
                    <div className="item-row-actions">
                      <button
                        type="button"
                        className={decision === 'overwrite' ? 'btn btn-primary' : 'btn'}
                        data-testid={`conflict-overwrite-${artifact.kind}-${artifact.id}`}
                        onClick={() => setDecision(artifact.kind, artifact.id, 'overwrite')}
                      >
                        Overwrite
                      </button>
                      <button
                        type="button"
                        className={decision === 'skip' ? 'btn btn-primary' : 'btn'}
                        data-testid={`conflict-skip-${artifact.kind}-${artifact.id}`}
                        onClick={() => setDecision(artifact.kind, artifact.id, 'skip')}
                      >
                        Skip
                      </button>
                      <button
                        type="button"
                        className={decision === 'keep_both' ? 'btn btn-primary' : 'btn'}
                        data-testid={`conflict-keep-both-${artifact.kind}-${artifact.id}`}
                        onClick={() => setDecision(artifact.kind, artifact.id, 'keep_both')}
                      >
                        Keep both
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {outcomes && (
        <div>
          <h3>Import result</h3>
          <div className="item-list">
            {outcomes.map((outcome) => {
              const routedAgentId = outcome.deployed_as ?? outcome.id;
              return (
                <div className="item-row" data-role={`import-outcome-${outcome.kind}-${outcome.id}`} key={`${outcome.kind}:${outcome.id}`}>
                  <div className="item-row-main">
                    <span className="item-row-title">{outcome.id}</span>
                    <span className="item-row-meta">
                      {outcome.kind} · {outcome.status}
                      {outcome.deployed_as && ` · deployed as ${outcome.deployed_as}`}
                    </span>
                    <span className="item-row-meta">{outcome.detail}</span>
                    {outcome.status === 'deployed' && outcome.primary_routing_snippet && (
                      <div className="item-row-meta" data-role={`primary-routing-suggestion-${outcome.id}`} style={{ marginTop: 'var(--space-2)' }}>
                        <p style={{ margin: 0 }}>Suggested routing for Primary&apos;s SOUL.md:</p>
                        <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem' }}>{outcome.primary_routing_snippet}</pre>
                        <button
                          type="button"
                          className="btn"
                          data-testid={`apply-primary-routing-${outcome.id}`}
                          disabled={routingLoading === routedAgentId}
                          onClick={() => handleApplyPrimaryRouting(routedAgentId, outcome.primary_routing_snippet as string)}
                        >
                          {routingLoading === routedAgentId ? 'Applying…' : "Add to Primary's SOUL.md"}
                        </button>
                        {routingStatus[routedAgentId] && (
                          <span className="item-row-meta" style={{ marginLeft: 'var(--space-2)' }}>
                            {routingStatus[routedAgentId]}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Modal>
  );
}
