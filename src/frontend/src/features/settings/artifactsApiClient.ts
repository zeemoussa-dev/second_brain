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
const EXPORT_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

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
}

export interface ImportPreviewResult {
  manifest: unknown;
  artifacts: ImportArtifactPreview[];
  available_profiles: string[];
}

export interface ImportOutcome {
  kind: string;
  id: string;
  status: 'deployed' | 'skipped' | 'failed';
  deployed_as: string | null;
  detail: string;
}

export function previewImport(file: File): Promise<ImportPreviewResult> {
  const formData = new FormData();
  formData.append('file', file);
  return apiFetch('/artifacts/import/preview', { method: 'POST', body: formData });
}

export function commitImport(
  file: File,
  decisions: Record<string, 'overwrite' | 'skip' | 'keep_both'>,
  skillTargetProfiles: Record<string, string[]>,
): Promise<ImportOutcome[]> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('decisions', JSON.stringify(decisions));
  formData.append('skill_target_profiles', JSON.stringify(skillTargetProfiles));
  return apiFetch('/artifacts/import/commit', { method: 'POST', body: formData });
}
