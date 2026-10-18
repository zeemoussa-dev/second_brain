import { ApiError, apiFetch } from '../../api/client';

// The Operator Profile's two routes (REQ-SB-95-US-01-T05) -- a thin client
// over GET/PUT /operator/profile (app/api/operator_router.py), same apiFetch
// helper and same shape as workflowsApiClient.ts.
//
// Three backend contracts this client exists to keep visible to its screen:
//
// - **It is a SINGLETON, not a catalogue** (`ADR-032`). There is no list, no
//   create, no delete and no id anywhere in these types, because the backend
//   has no such route -- a client offering one would be describing an API
//   that does not exist.
// - **`own_address` is read, never written** (`ADR-038`). It arrives on the
//   read type carrying its own `read_only` flag and the surface that edits
//   it, and it is absent BY TYPE from the write body. The field cannot be
//   sent by accident, which is why the page cannot normally provoke the
//   backend's `409`.
// - **A `PUT` REPLACES the whole record.** An omitted field means "empty",
//   never "leave what was there", so every save sends every fact the
//   operator still wants.

/** One colleague as MEMBERSHIP: the email that reaches their real Person
 *  note in the vault, and the role they hold. Deliberately nothing else --
 *  the vault's Person note is the one place a person is described
 *  (`ADR-032`), and the backend refuses an entry carrying more. */
export interface OperatorTeamMember {
  email: string;
  role: string;
}

/** The operator's own address as the Profile returns it: READ from the
 *  `SELF_EMAIL` setting and owned by it. `read_only` is always `true` and
 *  `edited_at` names the surface that owns the value, so no reader has to
 *  hardcode that answer a second time. */
export interface MirroredOwnAddress {
  email: string;
  read_only: boolean;
  setting_key: string;
  edited_at: string;
}

/** `is_configured` is the honest answer to "has this install ever saved a
 *  Profile?". It is NOT the same question as "could the Profile be read" --
 *  a failed `GET` rejects this promise instead, and the two must stay
 *  different renderings (`SPRINT-091`'s rule). */
export interface OperatorProfile {
  name: string;
  other_email_addresses: string[];
  timezone: string;
  team: OperatorTeamMember[];
  own_address: MirroredOwnAddress;
  is_configured: boolean;
}

/** `own_address`, `self_email` and `is_configured` are the backend's and are
 *  absent here by type: the first two are refused `409` by name and the
 *  third is derived, so none of them is a thing a client may send. */
export interface OperatorProfileWriteBody {
  name: string;
  other_email_addresses: string[];
  timezone: string;
  team: OperatorTeamMember[];
}

export function fetchOperatorProfile(): Promise<OperatorProfile> {
  return apiFetch('/operator/profile');
}

export function saveOperatorProfile(body: OperatorProfileWriteBody): Promise<OperatorProfile> {
  return apiFetch('/operator/profile', {
    method: 'PUT',
    body: JSON.stringify(body),
  });
}

interface FastApiValidationEntry {
  loc?: unknown;
  msg?: unknown;
}

/** The field path FastAPI names in a `422`, as the operator reads it:
 *  `["body","team",1,"email"]` becomes `team.1.email`. The leading `body`
 *  is dropped -- it names the request, not a field anyone can correct. */
function fieldPathOf(entry: FastApiValidationEntry): string {
  if (!Array.isArray(entry.loc)) return '';
  return entry.loc
    .filter((segment, index) => !(index === 0 && segment === 'body'))
    .map((segment) => String(segment))
    .join('.');
}

/** The refusal sentence to show, verbatim where the backend wrote one.
 *
 *  The two routes refuse in two deliberately different shapes and this is
 *  the one place that knows both:
 *
 *  - a `409` carries `detail` as a STRING -- the backend's own sentence
 *    naming `SELF_EMAIL` and the surface that edits it. It is returned
 *    unchanged, because a generic "save failed" would drop the only part
 *    the operator can act on.
 *  - a `422` carries `detail` as a LIST of FastAPI validation errors, each
 *    with a `loc` path. Each is rendered as its field path plus FastAPI's
 *    own message, so the screen can say WHICH team row and WHICH field is
 *    wrong rather than "invalid input".
 */
export function describeOperatorProfileRefusal(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Request failed.';
  let parsed: { detail?: unknown };
  try {
    parsed = JSON.parse(error.message) as { detail?: unknown };
  } catch {
    // Not JSON (a proxy error page, a dropped connection) -- the raw body is
    // still the most honest thing available.
    return error.message;
  }
  if (typeof parsed.detail === 'string') return parsed.detail;
  if (Array.isArray(parsed.detail)) {
    const named = (parsed.detail as FastApiValidationEntry[]).map((entry) => {
      const path = fieldPathOf(entry);
      const message = typeof entry.msg === 'string' ? entry.msg : 'is not valid';
      return path === '' ? message : `${path} — ${message}`;
    });
    if (named.length > 0) return named.join(' · ');
  }
  return error.message;
}
