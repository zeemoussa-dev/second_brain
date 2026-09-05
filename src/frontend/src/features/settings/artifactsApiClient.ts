import { apiFetch, ApiError } from '../../api/client';

// Artifact inventory (REQ-SB-85-US-01) -- a thin client over the real,
// already-Done GET /artifacts endpoint (app/api/artifacts_router.py),
// same apiFetch helper every other settings client uses.

export type ArtifactKind = 'skill' | 'template' | 'agent' | 'pipeline';

export interface ArtifactSummary {
  kind: ArtifactKind;
  id: string;
  name: string;
  description: string;
}

export function fetchArtifacts(): Promise<ArtifactSummary[]> {
  return apiFetch('/artifacts');
}

// Export flow (REQ-SB-85-US-02-T05) -- a thin client over the real,
// already-Done POST /artifacts/export/{preview,commit} endpoints
// (app/api/artifacts_router.py, app/business/logic/artifact_export.py).

export interface ArtifactSelectionEntry {
  kind: ArtifactKind;
  id: string;
}

export interface ClosureEntry {
  kind: string;
  id: string;
  included_reason: 'selected' | 'dependency';
  depends_via: string | null;
}

export interface SecretFinding {
  artifact_kind: string;
  artifact_id: string;
  file_path: string;
  line: number;
  matched_pattern: string;
  snippet: string;
}

export interface ExportPreviewResult {
  closure: ClosureEntry[];
  secret_findings: SecretFinding[];
}

export function previewExport(selection: ArtifactSelectionEntry[]): Promise<ExportPreviewResult> {
  return apiFetch('/artifacts/export/preview', {
    method: 'POST',
    body: JSON.stringify({ selection }),
  });
}

// Same base-URL convention as api/client.ts's own apiFetch -- duplicated
// here (rather than importing a non-exported constant) because this call
// needs the raw Response to read it as a Blob; apiFetch always resolves
// via response.json().
const EXPORT_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001';

export async function commitExport(
  selection: ArtifactSelectionEntry[],
  secretDecisions: Record<string, string>,
): Promise<Blob> {
  const response = await fetch(`${EXPORT_BASE_URL}/artifacts/export/commit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ selection, secret_decisions: secretDecisions }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.blob();
}

// Import flow (REQ-SB-85-US-03-T06) -- a thin client over the real,
// already-Done POST /artifacts/import/{preview,commit} endpoints
// (app/api/artifacts_router.py, app/business/logic/artifact_import.py).
// Both routes are real `multipart/form-data` POSTs -- apiFetch already
// skips the JSON Content-Type override for a FormData body.

export interface ImportArtifactPreview {
  kind: string;
  id: string;
  conflicts: boolean;
  category: string | null;
  /** True when a bundled Skill script still resolves the App Database Folder
   *  at the old <vault>/.second-brain location. Importing it would overwrite
   *  the corrected version and can silently stop email capture from writing
   *  anything -- the exact regression that cost 54 emails on 2026-09-04. */
  stale_data_path?: boolean;
  stale_data_path_detail?: { message: string; files: string[] };
}

export interface AvailableSection {
  id: string;
  name: string;
}

export interface ImportPreviewResult {
  manifest: unknown;
  artifacts: ImportArtifactPreview[];
  available_profiles: string[];
  available_sections: AvailableSection[];
}

export interface ImportOutcome {
  kind: string;
  id: string;
  status: 'deployed' | 'skipped' | 'failed';
  deployed_as: string | null;
  detail: string;
  primary_routing_snippet: string | null;
}

// "__create_new__:<name>" prefix -- matches artifact_import.py's own
// _CREATE_NEW_SECTION_PREFIX exactly; a section decision either names a
// real, existing target section id as-is, or this sentinel to create one.
export const CREATE_NEW_SECTION_PREFIX = '__create_new__:';

export function previewImport(file: File): Promise<ImportPreviewResult> {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch('/artifacts/import/preview', { method: 'POST', body: formData });
}

export function commitImport(
  file: File,
  decisions: Record<string, 'overwrite' | 'skip' | 'keep_both'>,
  skillTargetProfiles: Record<string, string[]>,
  agentSectionDecisions: Record<string, string>,
): Promise<ImportOutcome[]> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('decisions', JSON.stringify(decisions));
  formData.append('skill_target_profiles', JSON.stringify(skillTargetProfiles));
  formData.append('agent_section_decisions', JSON.stringify(agentSectionDecisions));
  return apiFetch('/artifacts/import/commit', { method: 'POST', body: formData });
}

// Primary-routing apply (2026-09-03) -- a thin client over the real,
// already-Done POST /artifacts/import/apply-primary-routing endpoint.
// Separate, explicit, operator-triggered -- never called automatically
// as part of commitImport above.

export interface ApplyPrimaryRoutingResult {
  agent_id: string;
  applied: boolean;
  detail: string;
}

export function applyPrimaryRouting(agentId: string, snippet: string): Promise<ApplyPrimaryRoutingResult> {
  return apiFetch('/artifacts/import/apply-primary-routing', {
    method: 'POST',
    body: JSON.stringify({ agent_id: agentId, snippet }),
  });
}
