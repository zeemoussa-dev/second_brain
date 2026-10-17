import { apiFetch } from '../../api/client';

// Action catalogue (REQ-SB-95-US-02-T06) -- a thin client over the real
// GET/POST/PUT/DELETE /actions endpoints (app/api/actions_router.py),
// same apiFetch helper and same shape as artifactsApiClient.ts.

export type ActionImplementationKind = 'skill' | 'http' | 'ui';

export const ACTION_IMPLEMENTATION_KINDS: ActionImplementationKind[] = ['skill', 'http', 'ui'];

/** One row of GET /actions: the stored fields the catalogue lists, plus the
 *  live resolution status the backend recomputes on every read (never
 *  stored), plus the contributing plugin where there is one. */
export interface ActionCatalogueEntry {
  id: string;
  description: string;
  implementation_kind: ActionImplementationKind | null;
  status: 'resolves' | 'broken';
  reason: string | null;
  /** The plugin that registered this Action. Absent entirely on one this
   *  install stored itself, exactly as the backend sends it. A plugin's
   *  Action exists only while that plugin is loaded, so it has no file to
   *  edit and the backend refuses every write on it -- which is why the
   *  list renders it without edit/delete. */
  plugin_id?: string | null;
}

export interface ActionInputField {
  name: string;
  type: string;
  required: boolean;
  description: string;
}

/** The READ shape: GET /actions/{id} returns the Action entity, whose
 *  implementation is FLAT and names its kind in a `kind` field. */
export interface ActionImplementationRead {
  kind: ActionImplementationKind;
  skill_id: string;
  method: string;
  path: string;
  feature_key: string;
}

export interface ActionDetail {
  id: string;
  description: string;
  inputs: ActionInputField[];
  allowed_callers: string[];
  needs_confirmation: boolean;
  implementation: ActionImplementationRead | null;
  created_at: string;
  updated_at: string | null;
}

/** The WRITE shape: a save sends the kind as a KEY, because which keys are
 *  present is what the backend counts "exactly one implementation" over.
 *  Deliberately NOT the read shape above -- putting a GET body straight back
 *  names no kind key and is refused with the exactly-one message. */
export type ActionImplementationWrite =
  | { skill: { skill_id: string } }
  | { http: { method: string; path: string } }
  | { ui: { feature_key: string } };

/** `id` after creation, `created_at` and `updated_at` are owned by the
 *  backend and rejected on a write, so they are absent here by type. */
export interface ActionWriteBody {
  description: string;
  inputs: ActionInputField[];
  allowed_callers: string[];
  needs_confirmation: boolean;
  /** `null` means "named nothing", which the backend refuses with its own
   *  exactly-one message -- the screen never refuses the save itself. */
  implementation: ActionImplementationWrite | null;
}

export function fetchActions(): Promise<ActionCatalogueEntry[]> {
  return apiFetch('/actions');
}

export function fetchAction(actionId: string): Promise<ActionDetail> {
  return apiFetch(`/actions/${encodeURIComponent(actionId)}`);
}

export function createAction(actionId: string, body: ActionWriteBody): Promise<ActionDetail> {
  return apiFetch('/actions', {
    method: 'POST',
    body: JSON.stringify({ id: actionId, ...body }),
  });
}

export function updateAction(actionId: string, body: ActionWriteBody): Promise<ActionDetail> {
  return apiFetch(`/actions/${encodeURIComponent(actionId)}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

export function deleteAction(actionId: string): Promise<{ deleted: boolean }> {
  return apiFetch(`/actions/${encodeURIComponent(actionId)}`, { method: 'DELETE' });
}
