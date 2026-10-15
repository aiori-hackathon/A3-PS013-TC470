const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function getToken(): string | null {
  return localStorage.getItem('cybertrace_token')
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem('cybertrace_token', token)
  else localStorage.removeItem('cybertrace_token')
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      // response had no JSON body; fall back to statusText
    }
    throw new ApiError(detail || 'Request failed', res.status)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

async function requestForm<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken()
  const headers = new Headers()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  // Content-Type is deliberately left unset so the browser sets the
  // multipart boundary itself.

  const res = await fetch(`${API_BASE_URL}${path}`, { method: 'POST', headers, body: formData })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      // response had no JSON body; fall back to statusText
    }
    throw new ApiError(detail || 'Request failed', res.status)
  }

  return (await res.json()) as T
}

/** Fetches a binary file with the auth header attached, returning a Blob
 * and the filename from the Content-Disposition header (falls back to a
 * generic name if the header is missing or unparsable). */
async function requestDownload(
  path: string,
): Promise<{ blob: Blob; filename: string | null }> {
  const token = getToken()
  const headers = new Headers()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(`${API_BASE_URL}${path}`, { method: 'GET', headers })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      // ignore
    }
    throw new ApiError(detail || 'Download failed', res.status)
  }

  const disposition = res.headers.get('Content-Disposition')
  const match = disposition?.match(/filename="?([^"]+)"?/)
  return { blob: await res.blob(), filename: match ? match[1] : null }
}

export const api = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  postForm: <T>(path: string, formData: FormData) => requestForm<T>(path, formData),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
  download: (path: string) => requestDownload(path),
}
