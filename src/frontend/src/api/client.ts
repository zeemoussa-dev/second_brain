const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  // A FormData body (file upload) must NOT get an explicit Content-Type --
  // the browser sets its own multipart boundary automatically, and an
  // override here would break it.
  const isFormData = init?.body instanceof FormData;
  const response = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { ...(isFormData ? {} : { 'Content-Type': 'application/json' }), ...init?.headers },
  });
  if (!response.ok) {
    throw new ApiError(response.status, await response.text());
  }
  return response.json() as Promise<T>;
}
