import { apiFetch, ApiError } from '../../api/client';
import type { SectionSummary } from '../agents-map/layoutAgents';

export type { SectionSummary };

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
  fields: { name?: string; icon?: string; color?: string; description?: string },
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

export interface ProviderSummary {
  id: string;
  name: string;
  endpoint: string;
  model: string;
  credential_set: boolean;
  is_default: boolean;
  has_real_client: boolean;
  agent_ids: string[];
}

export function fetchProviders(): Promise<ProviderSummary[]> {
  return apiFetch<ProviderSummary[]>('/providers');
}

export interface ProviderFormFields {
  name: string;
  endpoint: string;
  credential: string;
  model: string;
}

export function createProvider(fields: ProviderFormFields): Promise<ProviderSummary> {
  return apiFetch<ProviderSummary>('/providers', {
    method: 'POST',
    body: JSON.stringify(fields),
  });
}

export function updateProvider(
  providerId: string,
  fields: Partial<ProviderFormFields>,
): Promise<ProviderSummary> {
  return apiFetch<ProviderSummary>(`/providers/${providerId}`, {
    method: 'PATCH',
    body: JSON.stringify(fields),
  });
}

export async function removeProvider(providerId: string): Promise<DeleteResult> {
  try {
    await apiFetch<{ deleted: boolean }>(`/providers/${providerId}`, { method: 'DELETE' });
    return { ok: true };
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      const detail = JSON.parse(error.message) as { detail: string };
      return { ok: false, message: detail.detail };
    }
    throw error;
  }
}
