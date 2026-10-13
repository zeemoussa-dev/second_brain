// 8001 is the port `tools\run-backend.cmd` actually serves on, so this default
// has to track it. It said 8000 until 2026-09-04, which meant a fresh clone --
// where the `.env.local` carrying the override is gitignored and therefore
// absent -- rendered a blank screen with only ERR_CONNECTION_REFUSED to go on.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001';

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
