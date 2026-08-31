import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router';
import {
  fetchArtifacts,
  previewExport,
  commitExport,
  previewImport,
  commitImport,
  type ArtifactKind,
  type ArtifactSummary,
  type ArtifactSelectionEntry,
  type ExportPreviewResult,
  type SecretFinding,
  type ImportPreviewResult,
  type ImportOutcome,
} from '../features/settings/artifactsApiClient';
import { ApiError } from '../api/client';

// Cross-type artifact browser + multi-select (REQ-SB-85-US-01-T02) --
// functional-first per the story's own operator-overridden gate_reason:
// reuses the already-approved .item-list/.item-row family
// (SettingsVaultTemplatesPage.tsx/SettingsSectionsPage.tsx) for each row;
// the cross-type grouping + checkbox multi-select is genuinely new
// interaction with no prior approved visual precedent
// (net-new-design-needed, deferred to a later /design pass).

const KIND_ORDER: ArtifactKind[] = ['skill', 'template', 'agent', 'pipeline'];
const KIND_LABELS: Record<ArtifactKind, string> = {
  skill: 'Skills',
  template: 'Templates',
  agent: 'Agents',
  pipeline: 'Pipelines',
};

// The selection shape US-02 (Export) / US-03 (Import) both read/write once
// their own frontend tasks wire trigger buttons onto this page -- keyed by
// kind so a per-kind count is a plain Set.size read, no re-derivation.
type SelectionState = Record<ArtifactKind, Set<string>>;

function emptySelection(): SelectionState {
  return { skill: new Set(), template: new Set(), agent: new Set(), pipeline: new Set() };
}

// A per-finding decision, keyed by the SAME "{file_path}:{line}" identity
// artifact_secret_scan.py::_finding_key uses server-side -- see
// findingKey() below.
type SecretDecisionValue = 'redact' | 'keep';

function findingKey(finding: SecretFinding): string {
  return `${finding.file_path}:${finding.line}`;
}

// Best-effort extraction of FastAPI's own {"detail": "..."} JSON body out
// of the raw response text ApiError carries -- falls back to the raw text
// for a non-JSON error body rather than ever swallowing it silently.
// Shared by both Export and Import flows (T06 reuses this unchanged).
function extractErrorDetail(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message) as { detail?: unknown };
      if (typeof parsed.detail === 'string') {
        return parsed.detail;
      }
    } catch {
      // Not JSON -- fall through to the raw message below.
    }
    return error.message;
  }
  return 'Request failed.';
}

function triggerBlobDownload(blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `second-brain-export-${new Date().toISOString().replace(/[:.]/g, '-')}.sbf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function SettingsArtifactsPage() {
  const [artifacts, setArtifacts] = useState<ArtifactSummary[] | null>(null);
  const [selection, setSelection] = useState<SelectionState>(emptySelection());
  const [exportPreview, setExportPreview] = useState<ExportPreviewResult | null>(null);
  const [secretDecisions, setSecretDecisions] = useState<Record<string, SecretDecisionValue>>({});
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  // Import flow (REQ-SB-85-US-03-T06) -- independent of `selection` above;
  // import operates entirely on the uploaded file's own bundled contents.
  const [importUploadOpen, setImportUploadOpen] = useState(false);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<ImportPreviewResult | null>(null);
  const [importDecisions, setImportDecisions] = useState<Record<string, 'overwrite' | 'skip' | 'keep_both'>>({});
  const [importSkillTargetProfiles, setImportSkillTargetProfiles] = useState<Record<string, string[]>>({});
  const [importOutcomes, setImportOutcomes] = useState<ImportOutcome[] | null>(null);
  const [importLoading, setImportLoading] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);

  useEffect(() => {
    fetchArtifacts().then(setArtifacts);
  }, []);

  const groupedByKind = useMemo(() => {
    const groups: Record<ArtifactKind, ArtifactSummary[]> = { skill: [], template: [], agent: [], pipeline: [] };
    for (const artifact of artifacts ?? []) {
      groups[artifact.kind].push(artifact);
    }
    return groups;
  }, [artifacts]);

  const totalSelected = KIND_ORDER.reduce((sum, kind) => sum + selection[kind].size, 0);

  function toggleArtifact(kind: ArtifactKind, id: string) {
    setSelection((previous) => {
      const nextKindSet = new Set(previous[kind]);
      if (nextKindSet.has(id)) {
        nextKindSet.delete(id);
      } else {
        nextKindSet.add(id);
      }
      return { ...previous, [kind]: nextKindSet };
    });
  }

  function clearSelection() {
    setSelection(emptySelection());
  }

  function selectionToPayload(): ArtifactSelectionEntry[] {
    return KIND_ORDER.flatMap((kind) => Array.from(selection[kind]).map((id) => ({ kind, id })));
  }

  function resetExportFlow() {
    setExportPreview(null);
    setSecretDecisions({});
    setExportError(null);
  }

  async function handleRequestExport() {
    setExportError(null);
    const result = await previewExport(selectionToPayload());
    setSecretDecisions({});
    setExportPreview(result);
  }

  function setFindingDecision(finding: SecretFinding, decision: SecretDecisionValue) {
    setSecretDecisions((previous) => ({ ...previous, [findingKey(finding)]: decision }));
  }

  async function handleCommitExport(decisions: Record<string, string>) {
    setExportError(null);
    setExportLoading(true);
    try {
      const blob = await commitExport(selectionToPayload(), decisions);
      triggerBlobDownload(blob);
      resetExportFlow();
    } catch (error) {
      setExportError(extractErrorDetail(error));
    } finally {
      setExportLoading(false);
    }
  }

  function handleCancelExport() {
    // The simpler, equally-correct shape per the task's own Objective:
    // never call /commit on cancel -- the backend never writes anything
    // on the SecretScanCancelledError path anyway, so a real round trip
    // adds nothing beyond resetting local state.
    resetExportFlow();
  }

  function importDecisionKey(kind: string, id: string): string {
    return `${kind}:${id}`;
  }

  async function handleImportFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] ?? null;
    event.target.value = ''; // Allows re-selecting the SAME file a second time (e.g. Scenario 3's re-upload) -- otherwise onChange never fires again for an identical path.
    if (!file) {
      return;
    }
    setImportFile(file);
    setImportError(null);
    setImportPreview(null);
    setImportOutcomes(null);
    setImportDecisions({});
    setImportSkillTargetProfiles({});
    try {
      const result = await previewImport(file);
      setImportPreview(result);
      // "default" pre-checked for every bundled Skill -- mirrors T05's own
      // documented backend default (skill_target_profiles.get(id) or ["default"]).
      const skillDefaults: Record<string, string[]> = {};
      for (const artifact of result.artifacts) {
        if (artifact.kind === 'skill') {
          skillDefaults[artifact.id] = ['default'];
        }
      }
      setImportSkillTargetProfiles(skillDefaults);
    } catch (error) {
      setImportError(extractErrorDetail(error));
    }
  }

  function setImportDecision(kind: string, id: string, decision: 'overwrite' | 'skip' | 'keep_both') {
    setImportDecisions((previous) => ({ ...previous, [importDecisionKey(kind, id)]: decision }));
  }

  function toggleImportSkillTargetProfile(id: string, profile: string) {
    setImportSkillTargetProfiles((previous) => {
      const current = new Set(previous[id] ?? []);
      if (current.has(profile)) {
        current.delete(profile);
      } else {
        current.add(profile);
      }
      return { ...previous, [id]: Array.from(current) };
    });
  }

  const importAllConflictsResolved = importPreview
    ? importPreview.artifacts
        .filter((artifact) => artifact.conflicts)
        .every((artifact) => Boolean(importDecisions[importDecisionKey(artifact.kind, artifact.id)]))
    : false;

  async function handleCommitImport() {
    if (!importFile) {
      return;
    }
    setImportError(null);
    setImportLoading(true);
    try {
      const outcomes = await commitImport(importFile, importDecisions, importSkillTargetProfiles);
      setImportOutcomes(outcomes);
    } catch (error) {
      setImportError(extractErrorDetail(error));
    } finally {
      setImportLoading(false);
    }
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Artifacts</h1>
      <p className="text-muted">
        Every real Skill, Template, Agent, and Pipeline in this deployment, browsable and
        multi-selectable across kinds — the selection this list builds feeds the Export flow.
      </p>

      <div className="card" style={{ marginBottom: 'var(--space-4)' }}>
        {totalSelected > 0 && (
          <div data-role="artifact-selection-summary">
            <strong>{totalSelected} selected</strong>
            {' — '}
            {KIND_ORDER.filter((kind) => selection[kind].size > 0)
              .map((kind) => `${selection[kind].size} ${KIND_LABELS[kind]}`)
              .join(', ')}
          </div>
        )}
        {totalSelected === 0 && <p className="text-muted">No artifacts selected.</p>}
        <button
          type="button"
          className="btn"
          data-testid="clear-selection"
          disabled={totalSelected === 0}
          onClick={clearSelection}
          style={{ marginTop: 'var(--space-2)' }}
        >
          Clear selection
        </button>
        <button
          type="button"
          className="btn btn-primary"
          data-testid="export-selected"
          disabled={totalSelected === 0}
          onClick={handleRequestExport}
          style={{ marginTop: 'var(--space-2)', marginLeft: 'var(--space-2)' }}
        >
          Export selected
        </button>
      </div>

      <div className="card" data-role="import-flow" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Import</h2>
        <p className="text-muted">
          Upload a real `.sbf` bundle to preview its contents and resolve any conflicts before
          deploying — import doesn't need a prior selection above.
        </p>
        <button
          type="button"
          className="btn btn-primary"
          data-testid="import-trigger"
          onClick={() => setImportUploadOpen(true)}
        >
          Import…
        </button>

        {importUploadOpen && (
          <div style={{ marginTop: 'var(--space-2)' }}>
            <input type="file" accept=".sbf" data-testid="import-file-input" onChange={handleImportFileChange} />
          </div>
        )}

        {importError && (
          <p data-role="import-error" style={{ color: 'var(--color-danger)', marginTop: 'var(--space-2)' }}>
            {importError}
          </p>
        )}

        {importPreview && (
          <div data-role="import-contents-preview" style={{ marginTop: 'var(--space-2)' }}>
            <h3>Bundle contents</h3>
            <div className="item-list">
              {importPreview.artifacts.map((artifact) => {
                const decision = importDecisions[importDecisionKey(artifact.kind, artifact.id)];
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
                          {importPreview.available_profiles.map((profile) => (
                            <label key={profile} style={{ marginLeft: 'var(--space-2)' }}>
                              <input
                                type="checkbox"
                                data-testid={`skill-target-profile-${artifact.id}-${profile}`}
                                checked={(importSkillTargetProfiles[artifact.id] ?? []).includes(profile)}
                                onChange={() => toggleImportSkillTargetProfile(artifact.id, profile)}
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
                          onClick={() => setImportDecision(artifact.kind, artifact.id, 'overwrite')}
                        >
                          Overwrite
                        </button>
                        <button
                          type="button"
                          className={decision === 'skip' ? 'btn btn-primary' : 'btn'}
                          data-testid={`conflict-skip-${artifact.kind}-${artifact.id}`}
                          onClick={() => setImportDecision(artifact.kind, artifact.id, 'skip')}
                        >
                          Skip
                        </button>
                        <button
                          type="button"
                          className={decision === 'keep_both' ? 'btn btn-primary' : 'btn'}
                          data-testid={`conflict-keep-both-${artifact.kind}-${artifact.id}`}
                          onClick={() => setImportDecision(artifact.kind, artifact.id, 'keep_both')}
                        >
                          Keep both
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <button
              type="button"
              className="btn btn-primary"
              data-testid="import-commit"
              disabled={importLoading || !importAllConflictsResolved}
              onClick={handleCommitImport}
              style={{ marginTop: 'var(--space-2)' }}
            >
              {importLoading ? 'Importing…' : 'Commit import'}
            </button>
          </div>
        )}

        {importOutcomes && (
          <div style={{ marginTop: 'var(--space-2)' }}>
            <h3>Import result</h3>
            <div className="item-list">
              {importOutcomes.map((outcome) => (
                <div
                  className="item-row"
                  data-role={`import-outcome-${outcome.kind}-${outcome.id}`}
                  key={`${outcome.kind}:${outcome.id}`}
                >
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
      </div>

      {exportPreview && (
        <div className="card" data-role="export-dependency-preview" style={{ marginBottom: 'var(--space-4)' }}>
          <h2>Export preview</h2>
          <p className="text-muted">
            Everything that will be included in the bundle, and why — nothing is written until
            you confirm below.
          </p>
          <div className="item-list">
            {exportPreview.closure.map((entry) => (
              <div className="item-row" key={`${entry.kind}:${entry.id}`}>
                <div className="item-row-main">
                  <span className="item-row-title">{entry.id}</span>
                  <span className="item-row-meta">
                    {KIND_LABELS[entry.kind as ArtifactKind]?.slice(0, -1) ?? entry.kind}
                    {' · '}
                    {entry.included_reason === 'selected'
                      ? 'directly selected'
                      : `included because: ${entry.depends_via}`}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {exportPreview.secret_findings.length === 0 && (
            <button
              type="button"
              className="btn btn-primary"
              data-testid="export-confirm"
              disabled={exportLoading}
              onClick={() => handleCommitExport({})}
              style={{ marginTop: 'var(--space-2)' }}
            >
              {exportLoading ? 'Exporting…' : 'Confirm export'}
            </button>
          )}
        </div>
      )}

      {exportPreview && exportPreview.secret_findings.length > 0 && (
        <div className="card" data-role="secret-scan-confirmation" style={{ marginBottom: 'var(--space-4)' }}>
          <h2>Secret-shaped content found</h2>
          <p className="text-muted">
            Decide what happens to each finding below — nothing is stripped silently, and no
            file is written until every finding has a decision.
          </p>
          <div className="item-list">
            {exportPreview.secret_findings.map((finding) => {
              const key = findingKey(finding);
              const decision = secretDecisions[key];
              return (
                <div className="item-row" key={key}>
                  <div className="item-row-main">
                    <span className="item-row-title">{finding.file_path}:{finding.line}</span>
                    <span className="item-row-meta">{finding.matched_pattern} — {finding.snippet}</span>
                  </div>
                  <div className="item-row-actions">
                    <button
                      type="button"
                      className={decision === 'redact' ? 'btn btn-primary' : 'btn'}
                      data-testid={`finding-redact-${key}`}
                      onClick={() => setFindingDecision(finding, 'redact')}
                    >
                      Redact
                    </button>
                    <button
                      type="button"
                      className={decision === 'keep' ? 'btn btn-primary' : 'btn'}
                      data-testid={`finding-keep-${key}`}
                      onClick={() => setFindingDecision(finding, 'keep')}
                    >
                      Keep as-is
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
          <div style={{ marginTop: 'var(--space-2)' }}>
            <button type="button" className="btn" data-testid="export-cancel" onClick={handleCancelExport}>
              Cancel export
            </button>
            <button
              type="button"
              className="btn btn-primary"
              data-testid="export-confirm"
              disabled={
                exportLoading ||
                exportPreview.secret_findings.some((finding) => !secretDecisions[findingKey(finding)])
              }
              onClick={() => handleCommitExport(secretDecisions)}
              style={{ marginLeft: 'var(--space-2)' }}
            >
              {exportLoading ? 'Exporting…' : 'Confirm export'}
            </button>
          </div>
        </div>
      )}

      {exportError && (
        <div className="card" data-role="export-error" style={{ marginBottom: 'var(--space-4)' }}>
          <p style={{ color: 'var(--color-danger)' }}>{exportError}</p>
        </div>
      )}

      {artifacts === null && <p className="text-muted">Loading...</p>}

      {artifacts !== null &&
        KIND_ORDER.map((kind) => (
          <div className="card" key={kind} style={{ marginBottom: 'var(--space-4)' }}>
            <h2>{KIND_LABELS[kind]}</h2>
            <div className="item-list">
              {groupedByKind[kind].map((artifact) => (
                <div className="item-row" key={artifact.id}>
                  <div className="item-row-main">
                    <span className="item-row-title">{artifact.name}</span>
                    <span className="item-row-meta">{KIND_LABELS[kind].slice(0, -1)} · {artifact.id}</span>
                    {artifact.description && <span className="item-row-meta">{artifact.description}</span>}
                  </div>
                  <div className="item-row-actions">
                    <input
                      type="checkbox"
                      data-testid={`artifact-checkbox-${kind}-${artifact.id}`}
                      checked={selection[kind].has(artifact.id)}
                      onChange={() => toggleArtifact(kind, artifact.id)}
                    />
                  </div>
                </div>
              ))}
              {groupedByKind[kind].length === 0 && (
                <p className="text-muted" data-role={`artifact-empty-${kind}`}>
                  No {KIND_LABELS[kind]} yet.
                </p>
              )}
            </div>
          </div>
        ))}
    </>
  );
}
