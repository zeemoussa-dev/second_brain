// 8001 is the port `tools\run-backend.cmd` actually serves on, so this default
// has to track it. It said 8000 until 2026-09-04, which meant a fresh clone --
// where the `.env.local` carrying the override is gitignored and therefore
// absent -- rendered a blank screen with only ERR_CONNECTION_REFUSED to go on.
/** The backend's origin, with one correction applied.
 *
 * `localhost` and `127.0.0.1` are the same machine but DIFFERENT SITES
 * to a browser's cookie rules. The configured base says `127.0.0.1:8001`
 * while the dev server serves the page from `localhost:5173`, so the
 * session cookie -- `SameSite=Lax`, as it should be -- was set by one
 * site and never sent back by the other: sign-in returned 200, the
 * cookie was stored, and the very next request was anonymous again. The
 * symptom is "clicking Sign in does nothing", with no error anywhere,
 * because nothing failed (REQ-SB-101, found 2026-10-21).
 *
 * So when BOTH the page and the configured backend are loopback and
 * they merely spell it differently, the backend is addressed by the
 * spelling the page is using. A real deployment -- any non-loopback
 * host -- is left exactly as configured, because there the two being
 * different origins is the point rather than an accident.
 */
const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '[::1]', '::1']);

function resolveBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001';
  if (typeof window === 'undefined') return configured;
  try {
    const backend = new URL(configured);
    const pageHost = window.location.hostname;
    if (
      LOOPBACK_HOSTS.has(backend.hostname) &&
      LOOPBACK_HOSTS.has(pageHost) &&
      backend.hostname !== pageHost
    ) {
      backend.hostname = pageHost;
      return backend.origin;
    }
  } catch {
    // An unparseable VITE_API_BASE_URL is the operator's to fix, and a
    // thrown error here would blank the whole app before anything could
    // say so. Use it as given and let the failing request report it.
  }
  return configured;
}

/** The backend origin every client in the app shares. Exported so the
 * handful of places that build a URL themselves -- a stream, an <img
 * src>, a download link -- use the same corrected origin, rather than
 * each re-reading the env var and reintroducing the cookie mismatch
 * above on their own path. */
export const API_BASE_URL = resolveBaseUrl();

const BASE_URL = API_BASE_URL;

/** The absolute URL of a backend path, for an <a href> or <img src> that the
 * browser fetches for itself rather than `apiFetch` returning JSON. */
export function apiUrl(path: string): string {
  return `${BASE_URL}${path}`;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

// One in-flight GET per path, shared by everyone who asks for it while it is in
// the air (`BUG-086`). The Agents Map mounts several components that each load
// the same data, and React's StrictMode runs every effect twice in dev, so
// opening it fired `/agents` twice, `/sections` twice and `/pipelines` four
// times -- all at the same instant, where they then queued behind each other:
// the second `/agents` took 5.5s against 1.4s on its own.
//
// Deliberately NOT a cache: the entry is dropped the moment the request settles,
// so a later call still goes to the backend and nothing serves a stale answer. A
// request that carries a body, or any method other than GET, is never shared.
const inFlightGets = new Map<string, Promise<unknown>>();

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const isSharableGet = !init?.body && (!init?.method || init.method.toUpperCase() === 'GET');
  if (isSharableGet) {
    const existing = inFlightGets.get(path);
    if (existing) return existing as Promise<T>;
  }

  // A FormData body (file upload) must NOT get an explicit Content-Type --
  // the browser sets its own multipart boundary automatically, and an
  // override here would break it.
  const isFormData = init?.body instanceof FormData;
  const request = (async () => {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      // REQ-SB-101: the session is an httponly cookie the backend sets, and
      // the backend is a different origin (:8001 against this :5173), so
      // `fetch` omits it unless asked. Set here, once, rather than in each
      // feature's client -- a caller that forgot it would be anonymous and
      // get a 401 that looks like a permissions bug rather than a missing
      // flag. `apiUrl` callers (an <a href> or <img src>) are unaffected:
      // the browser sends cookies for those itself.
      credentials: 'include',
      headers: { ...(isFormData ? {} : { 'Content-Type': 'application/json' }), ...init?.headers },
    });
    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }
    return response.json() as Promise<T>;
  })();

  if (!isSharableGet) return request;
  inFlightGets.set(path, request);
  try {
    return await request;
  } finally {
    inFlightGets.delete(path);
  }
}
