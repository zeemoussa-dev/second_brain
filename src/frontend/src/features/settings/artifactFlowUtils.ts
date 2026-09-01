import { ApiError } from '../../api/client';

// Shared by ArtifactExportModal.tsx/ArtifactImportModal.tsx — best-effort
// extraction of FastAPI's own {"detail": "..."} JSON body out of the raw
// response text ApiError carries, falling back to the raw text for a
// non-JSON error body rather than ever swallowing it silently.
export function extractErrorDetail(error: unknown): string {
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

export function triggerBlobDownload(blob: Blob, filename = `second-brain-export-${new Date().toISOString().replace(/[:.]/g, '-')}.sbf`) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}
