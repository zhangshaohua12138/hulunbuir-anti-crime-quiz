const base = import.meta.env.VITE_API_BASE || ''

export class ApiError extends Error {
  status: number
  constructor(message: string, status = 400) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {})
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const response = await fetch(base + path, {
    ...options,
    headers,
    credentials: 'include',
  })
  const text = await response.text()
  let data: unknown = null
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = null
  }
  if (!response.ok) {
    const message = (data && typeof data === 'object' && 'error' in data && String((data as { error: unknown }).error)) || `请求失败 (${response.status})`
    throw new ApiError(message, response.status)
  }
  return data as T
}
