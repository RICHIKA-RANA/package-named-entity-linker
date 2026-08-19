export interface Namespace {
  name: string
  description: string | null
  created_at: string
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function safeDetail(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body?.detail === 'string') return body.detail
  } catch {
    // response body wasn't JSON - fall through to the generic message
  }
  return `Request failed with status ${response.status}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init)

  if (!response.ok) {
    throw new ApiError(response.status, await safeDetail(response))
  }

  return response.json() as Promise<T>
}

export function listNamespaces(): Promise<Namespace[]> {
  return request<Namespace[]>('/api/namespaces')
}

export function createNamespace(
  name: string,
  description?: string,
): Promise<Namespace> {
  return request<Namespace>('/api/namespaces', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description: description || null }),
  })
}

export function getNamespace(name: string): Promise<Namespace> {
  return request<Namespace>(`/api/namespaces/${encodeURIComponent(name)}`)
}
