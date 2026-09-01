import { useState } from 'react';
import { Modal } from './Modal';
import {
  commitExport,
  type ArtifactKind,
  type ArtifactSelectionEntry,
  type ExportPreviewResult,
  type SecretFinding,
} from './artifactsApiClient';
import { extractErrorDetail, triggerBlobDownload } from './artifactFlowUtils';

const KIND_LABELS: Record<ArtifactKind, string> = {
  skill: 'Skill', template: 'Template', agent: 'Agent', pipeline: 'Pipeline',
};

type SecretDecisionValue = 'redact' | 'keep';

function findingKey(finding: SecretFinding): string {
  return `${finding.file_path}:${finding.line}`;
}

// Export confirmation, as a popup (operator, 2026-09-01: "The Confirmation
// should be a popup not in the header of the Page") — the closure preview
// and any secret-scan findings both render in ONE modal now, rather than
// as inline cards that used to push the rest of the page down. `preview`
// is the same live closure SettingsArtifactsPage.tsx already fetches to
// drive the locked-dependency checkboxes in the side panel — reused here
// rather than re-fetched, since the selection can't change while this
// modal has the page underneath it blocked.
interface ArtifactExportModalProps {
  selection: ArtifactSelectionEntry[];
  preview: ExportPreviewResult;
  onClose: () => void;
  onExported: () => void;
}

export function ArtifactExportModal({ selection, preview, onClose, onExported }: ArtifactExportModalProps) {
  const [secretDecisions, setSecretDecisions] = useState<Record<string, SecretDecisionValue>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setFindingDecision(finding: SecretFinding, decision: SecretDecisionValue) {
    setSecretDecisions((previous) => ({ ...previous, [findingKey(finding)]: decision }));
  }

  const allFindingsDecided = preview.secret_findings.every((finding) => Boolean(secretDecisions[findingKey(finding)]));

  async function handleConfirm() {
    setError(null);
    setLoading(true);
    try {
      const blob = await commitExport(selection, secretDecisions);
      triggerBlobDownload(blob);
      onExported();
    } catch (commitError) {
      setError(extractErrorDetail(commitError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Modal
      title="Export"
      description="Everything below will be included in the bundle, and why — nothing is written until you confirm."
      onClose={onClose}
      footer={
        <>
          <button type="button" className="btn" data-testid="export-cancel" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            data-testid="export-confirm"
            disabled={loading || !allFindingsDecided}
            onClick={handleConfirm}
          >
            {loading ? 'Exporting…' : 'Confirm export'}
          </button>
        </>
      }
    >
      <div className="item-list" data-role="export-dependency-preview">
        {preview.closure.map((entry) => (
          <div className="item-row" key={`${entry.kind}:${entry.id}`}>
            <div className="item-row-main">
              <span className="item-row-title">{entry.id}</span>
              <span className="item-row-meta">
                {KIND_LABELS[entry.kind as ArtifactKind] ?? entry.kind}
                {' · '}
                {entry.included_reason === 'selected' ? 'directly selected' : `included because: ${entry.depends_via}`}
              </span>
            </div>
          </div>
        ))}
      </div>

      {preview.secret_findings.length > 0 && (
        <div data-role="secret-scan-confirmation" style={{ marginTop: 'var(--space-4)' }}>
          <h3>Secret-shaped content found</h3>
          <p className="text-muted">
            Decide what happens to each finding — nothing is stripped silently, and export stays
            blocked until every finding has a decision.
          </p>
          <div className="item-list">
            {preview.secret_findings.map((finding) => {
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
        </div>
      )}

      {error && (
        <p data-role="export-error" style={{ color: 'var(--color-danger)', marginTop: 'var(--space-3)' }}>
          {error}
        </p>
      )}
    </Modal>
  );
}
