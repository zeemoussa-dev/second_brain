import { useState } from 'react';
import { Modal } from './Modal';
import { previewImport, commitImport, type ImportPreviewResult, type ImportOutcome } from './artifactsApiClient';
import { extractErrorDetail } from './artifactFlowUtils';

function decisionKey(kind: string, id: string): string {
  return `${kind}:${id}`;
}

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
  const [outcomes, setOutcomes] = useState<ImportOutcome[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  async function handleCommit() {
    if (!file) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await commitImport(file, decisions, skillTargetProfiles);
      setOutcomes(result);
    } catch (commitError) {
      setError(extractErrorDetail(commitError));
    } finally {
      setLoading(false);
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
            {outcomes.map((outcome) => (
              <div className="item-row" data-role={`import-outcome-${outcome.kind}-${outcome.id}`} key={`${outcome.kind}:${outcome.id}`}>
                <div className="item-row-main">
                  <span className="item-row-title">{outcome.id}</span>
                  <span className="item-row-meta">
                    {outcome.kind} · {outcome.status}
                    {outcome.deployed_as && ` · deployed as ${outcome.deployed_as}`}
                  </span>
                  <span className="item-row-meta">{outcome.detail}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Modal>
  );
}
