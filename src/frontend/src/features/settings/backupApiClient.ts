import { ApiError } from '../../api/client';

// Backup/Restore (Settings > Backup) -- real Hermes structural backup
// (Agents/Profiles, Cron, Skills) + the app's own matching data, as a
// downloadable *.sbb archive. Same fetch-for-a-Blob shape
// vaultApiClient.ts::exportVaultData already established (apiFetch
// always resolves via response.json(), so a binary download bypasses it
// and re-implements the same ApiError(status, text) mapping directly).

const BACKUP_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export interface RestoreResult {
  status: string;
  profiles: Record<string, { state: string; files_overlaid: number }>;
  cron: {
    added: { id: string; name: string }[];
    skipped_existing: { id: string; name: string }[];
  };
  second_brain_data: Record<string, { status: string; files?: number; reason?: string; existing_files?: number }>;
  path_rewrite: {
    vault: { from: string; to: string };
    hermes_home: { from: string; to: string };
    files_rewritten: number;
  };
  manual_follow_ups: string[];
}

export interface RestoreRefused {
  status: 'refused';
  problems: string[];
}

export interface RestoreFailedMidWay {
  status: 'failed_mid_restore';
  error: string;
}

export async function exportBackup(): Promise<Blob> {
  const response = await fetch(`${BACKUP_BASE_URL}/backup/export`, { method: 'POST' });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.blob();
}

export async function restoreBackup(file: File, force: boolean): Promise<RestoreResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('force', force ? 'true' : 'false');
  const response = await fetch(`${BACKUP_BASE_URL}/backup/restore`, { method: 'POST', body: formData });
  const body = await response.json();
  if (!response.ok) {
    // FastAPI wraps our own detail (either RestoreRefused/RestoreFailedMidWay
    // or a plain string) under {"detail": ...} -- unwrap it so the caller
    // always sees the real script's own structured result, not FastAPI's
    // own envelope.
    throw new ApiError(response.status, JSON.stringify(body.detail ?? body));
  }
  return body as RestoreResult;
}

export function triggerSbbDownload(blob: Blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `second-brain-backup-${new Date().toISOString().replace(/[:.]/g, '-')}.sbb`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
