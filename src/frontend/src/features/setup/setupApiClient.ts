import { apiFetch } from '../../api/client';

export interface SetupField {
  key: string;
  label: string;
  icon: string;
  description: string;
  /** A configured secret comes back as a bullet mask, never the real value.
   *  Submitting the mask unchanged is a no-op server-side, so a step the
   *  operator skipped can't wipe a working credential. */
  value: string;
  secret: boolean;
  required: boolean;
}

export interface SetupStep {
  id: string;
  title: string;
  blurb: string;
  fields: SetupField[];
}

export interface SetupStatus {
  setup_required: boolean;
  missing: string[];
  steps: SetupStep[];
}

export interface CheckResult {
  ok: boolean;
  detail: string;
}

export interface HermesCheck extends CheckResult {
  key: string;
  label: string;
}

export interface HermesHealth {
  home_path: string;
  checks: HermesCheck[];
  all_ok: boolean;
  read_only: boolean;
}

export function getSetupStatus(): Promise<SetupStatus> {
  return apiFetch<SetupStatus>('/setup/status');
}

export function getHermesHealth(vaultPath: string): Promise<HermesHealth> {
  // The typed-but-unsaved vault path, so the agreement row reflects what is
  // about to be saved rather than the (empty, on a fresh install) setting.
  return apiFetch<HermesHealth>(`/setup/hermes-health?vault_path=${encodeURIComponent(vaultPath)}`);
}

export function validateField(field: string, value: string): Promise<CheckResult> {
  return apiFetch<CheckResult>('/setup/validate', {
    method: 'POST',
    body: JSON.stringify({ field, value }),
  });
}

export function testCompass(values: Record<string, string>): Promise<CheckResult> {
  return apiFetch<CheckResult>('/setup/test-compass', {
    method: 'POST',
    body: JSON.stringify({
      compass_base_url: values.compass_base_url ?? '',
      compass_api_key: values.compass_api_key ?? '',
      compass_model: values.compass_model ?? '',
    }),
  });
}

export interface SaveResult {
  ok: boolean;
  restart_required: boolean;
  /** Whether the vault path also reached Hermes' own .env as
   *  OBSIDIAN_VAULT_PATH. Reported separately because the app's settings
   *  save fine even when Hermes isn't installed. */
  hermes_vault_sync: { ok: boolean; detail: string; files_written: number };
}

export function saveSetup(values: Record<string, string>): Promise<SaveResult> {
  return apiFetch<SaveResult>('/setup/save', {
    method: 'POST',
    body: JSON.stringify({ values }),
  });
}

export function restartBackend(): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>('/setup/restart', { method: 'POST' });
}
