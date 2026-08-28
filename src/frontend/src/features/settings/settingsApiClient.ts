import { apiFetch, ApiError } from '../../api/client';
import type { SectionSummary } from '../agents-map/layoutAgents';

export type { SectionSummary };

// System settings page (Settings > System, 2026-08-27) -- five real,
// system-wide config values read straight from app.config.settings, never
// fabricated. Editing writes to .env and requires a restart to apply.
export interface SystemSettingFieldStatus {
  ok: boolean;
  detail: string;
}

export interface SystemSettingField {
  key: string;
  label: string;
  icon: string;
  description: string;
  value: string;
  status: SystemSettingFieldStatus;
}

export function fetchSystemSettings(): Promise<{ fields: SystemSettingField[] }> {
  return apiFetch<{ fields: SystemSettingField[] }>('/settings/system');
}

export function testSystemField(field: string): Promise<SystemSettingFieldStatus> {
  return apiFetch<SystemSettingFieldStatus>(`/settings/system/test/${field}`, { method: 'POST' });
}

export type UpdateSystemSettingsResult =
  | { ok: true; restart_required: true }
  | { ok: false; message: string };

export async function updateSystemSettings(
  patch: Record<string, string>,
): Promise<UpdateSystemSettingsResult> {
  try {
    return await apiFetch<{ ok: true; restart_required: true }>('/settings/system', {
      method: 'PUT',
      body: JSON.stringify(patch),
    });
  } catch (error) {
    if (error instanceof ApiError && error.status === 400) {
      const detail = JSON.parse(error.message) as { detail: string };
      return { ok: false, message: detail.detail };
    }
    throw error;
  }
}

export function shutdownSystem(): Promise<{ ok: boolean }> {
  return apiFetch<{ ok: boolean }>('/settings/system/shutdown', { method: 'POST' });
}

export function fetchSections(): Promise<SectionSummary[]> {
  return apiFetch<SectionSummary[]>('/sections');
}

export function createSection(name: string): Promise<SectionSummary> {
  return apiFetch<SectionSummary>('/sections', {
    method: 'POST',
    body: JSON.stringify({ name }),
  });
}

export function renameSection(sectionId: string, name: string): Promise<SectionSummary> {
  return apiFetch<SectionSummary>(`/sections/${sectionId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  });
}

// 2026-08-23 -- the Section detail panel's own Settings tab (operator:
// "the Hub can be clicked and has its own Settings... Section Color and
// Icon, Description and Name"). Each field: omit = leave unchanged,
// "" = clear back to unset (same convention as updateAgentAssignment's
// icon/color).
export function updateSection(
  sectionId: string,
  fields: {
    name?: string; icon?: string; color?: string; subtitle?: string; description?: string;
    folders?: string[]; fallback_agent_id?: string;
  },
): Promise<SectionSummary> {
  return apiFetch<SectionSummary>(`/sections/${sectionId}`, {
    method: 'PATCH',
    body: JSON.stringify(fields),
  });
}

export type DeleteResult = { ok: true } | { ok: false; message: string };

export async function deleteSection(sectionId: string): Promise<DeleteResult> {
  try {
    await apiFetch<{ deleted: boolean }>(`/sections/${sectionId}`, { method: 'DELETE' });
    return { ok: true };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      const detail = JSON.parse(error.message) as { detail: string };
      return { ok: false, message: detail.detail };
    }
    throw error;
  }
}

