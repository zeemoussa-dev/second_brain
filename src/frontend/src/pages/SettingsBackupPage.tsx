import { useState } from 'react';
import { Link } from 'react-router';
import { ApiError } from '../api/client';
import { exportBackup, restoreBackup, triggerSbbDownload, type RestoreResult } from '../features/settings/backupApiClient';

// Backup/Restore (2026-09-03) -- a real Hermes structural backup
// (Agents/Profiles, Cron, Skills) + the app's own matching Registry/
// Pipeline data, as a downloadable *.sbb archive, for moving this whole
// deployment to a new machine. Deliberately excludes Hermes instance
// config (config.yaml) and every real secret -- operator: "Secrets is
// what i meant with settings." Restore is meant to run on the NEW
// machine, once Hermes is already installed and configured there with
// its OWN real secrets (Deployment.md Sections 1-2) -- this page is the
// thin UI over the already-tested tools/hermes_backup.py/
// hermes_restore.py CLI pair (MEMORY.md, 2026-09-03).

function extractErrorDetail(error: unknown): string {
  if (error instanceof ApiError) {
    try {
      const parsed = JSON.parse(error.message);
      if (parsed?.problems) {
        return `Refused: ${(parsed.problems as string[]).join('; ')}`;
      }
      if (parsed?.error) {
        return `Failed mid-restore: ${parsed.error}`;
      }
      if (typeof parsed === 'string') {
        return parsed;
      }
    } catch {
      // Not JSON -- fall through to the raw message below.
    }
    return error.message;
  }
  return 'Request failed.';
}

export function SettingsBackupPage() {
  const [exportLoading, setExportLoading] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [force, setForce] = useState(false);
  const [restoreLoading, setRestoreLoading] = useState(false);
  const [restoreError, setRestoreError] = useState<string | null>(null);
  const [restoreResult, setRestoreResult] = useState<RestoreResult | null>(null);

  async function handleExport() {
    setExportError(null);
    setExportLoading(true);
    try {
      const blob = await exportBackup();
      triggerSbbDownload(blob);
    } catch (error) {
      setExportError(extractErrorDetail(error));
    } finally {
      setExportLoading(false);
    }
  }

  async function handleRestore() {
    if (!selectedFile) return;
    setRestoreError(null);
    setRestoreResult(null);
    setRestoreLoading(true);
    try {
      const result = await restoreBackup(selectedFile, force);
      setRestoreResult(result);
    } catch (error) {
      setRestoreError(extractErrorDetail(error));
    } finally {
      setRestoreLoading(false);
    }
  }

  return (
    <>
      <p className="text-muted"><Link className="text-muted" to="/settings">&larr; Settings</Link></p>
      <h1>Backup &amp; Restore</h1>
      <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
        A full structural backup of this Hermes deployment — every Agent/Profile's own identity
        and Skills, real Cron jobs, and this app's own matching Registry/Pipeline data — as one
        portable <code>.sbb</code> file. Never includes Hermes config (model/provider settings) or
        any real secret; restore onto a new machine assumes Hermes is already installed and
        configured there with its own real secrets first.
      </p>

      <div className="card" data-role="backup-export" style={{ marginBottom: 'var(--space-4)' }}>
        <h2>Create backup</h2>
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          Downloads a <code>.sbb</code> of this machine's real Hermes structure right now.
        </p>
        <button type="button" className="btn btn-primary" data-testid="backup-export-button" disabled={exportLoading} onClick={handleExport}>
          {exportLoading ? 'Creating backup…' : 'Create backup'}
        </button>
        {exportError && (
          <p style={{ color: 'var(--color-danger)', marginTop: 'var(--space-2)' }} data-role="backup-export-error">
            {exportError}
          </p>
        )}
      </div>

      <div className="card" data-role="backup-restore">
        <h2>Restore from backup</h2>
        <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
          Overlays a <code>.sbb</code>'s own Agents/Profiles/Skills onto this machine's real Hermes
          install (creating any profile that doesn't exist yet), merges Cron jobs by id — a real job
          already on this machine is never overwritten — and rewrites every vault-path and
          Hermes-install-path reference to match this machine's own real paths.
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
          <input
            type="file"
            accept=".sbb"
            data-testid="backup-restore-file-input"
            onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <input
              type="checkbox"
              data-testid="backup-restore-force"
              checked={force}
              onChange={(event) => setForce(event.target.checked)}
            />
            Overwrite existing app data (Registry/Pipelines) if this vault already has some
          </label>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          data-testid="backup-restore-button"
          disabled={!selectedFile || restoreLoading}
          onClick={handleRestore}
        >
          {restoreLoading ? 'Restoring…' : 'Restore'}
        </button>

        {restoreError && (
          <p style={{ color: 'var(--color-danger)', marginTop: 'var(--space-3)' }} data-role="backup-restore-error">
            {restoreError}
          </p>
        )}

        {restoreResult && (
          <div data-role="backup-restore-result" style={{ marginTop: 'var(--space-4)' }}>
            <h3>Restore complete</h3>

            <p><strong>Profiles</strong></p>
            <ul>
              {Object.entries(restoreResult.profiles).map(([id, info]) => (
                <li key={id}>
                  {id} — {info.state === 'created' ? 'created fresh' : 'already existed, overlaid'} ({info.files_overlaid} files)
                </li>
              ))}
            </ul>

            <p><strong>Cron jobs</strong></p>
            <ul>
              {restoreResult.cron.added.map((job) => (
                <li key={job.id}>+ {job.name} ({job.id}) — added</li>
              ))}
              {restoreResult.cron.skipped_existing.map((job) => (
                <li key={job.id}>{job.name} ({job.id}) — already existed on this machine, left untouched</li>
              ))}
              {restoreResult.cron.added.length === 0 && restoreResult.cron.skipped_existing.length === 0 && (
                <li className="text-muted">No cron jobs in this backup.</li>
              )}
            </ul>

            <p><strong>Second Brain app data</strong></p>
            <ul>
              {Object.entries(restoreResult.second_brain_data).map(([kind, info]) => (
                <li key={kind}>
                  {kind}: {info.status}
                  {info.status === 'refused' && ` (${info.reason}, ${info.existing_files} existing files — check "Overwrite" and retry if you really want to replace them)`}
                  {info.status === 'restored' && ` (${info.files} files)`}
                </li>
              ))}
            </ul>

            <p><strong>Path rewrite</strong></p>
            <p className="text-muted" style={{ fontSize: 'var(--font-size-sm)' }}>
              {restoreResult.path_rewrite.files_rewritten} file(s) rewritten — vault path{' '}
              <code>{restoreResult.path_rewrite.vault.from}</code> → <code>{restoreResult.path_rewrite.vault.to}</code>,
              Hermes home <code>{restoreResult.path_rewrite.hermes_home.from}</code> →{' '}
              <code>{restoreResult.path_rewrite.hermes_home.to}</code>.
            </p>

            <p><strong>Still to do by hand</strong></p>
            <ul>
              {restoreResult.manual_follow_ups.map((step) => (
                <li key={step}><code>{step}</code></li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </>
  );
}
