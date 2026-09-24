const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    credentials: 'include',
  })
  if (!response.ok) {
    let message = `请求失败（${response.status}）`
    try {
      const data = (await response.json()) as {
        detail?: string | { message?: string; rows?: Array<{ row_number: number; errors: string[] }> }
      }
      if (typeof data.detail === 'string') message = data.detail
      else if (data.detail?.message) {
        const rowErrors = data.detail.rows?.map((row) => `第 ${row.row_number} 行：${row.errors.join('；')}`).join('；')
        message = rowErrors ? `${data.detail.message}：${rowErrors}` : data.detail.message
      }
    } catch {
      // 保留默认错误信息
    }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) }),
  patch: <T>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
  upload: <T>(path: string, file: File, fields: Record<string, string | string[]> = {}) => {
    const form = new FormData()
    form.append('file', file)
    for (const [key, value] of Object.entries(fields)) {
      for (const item of Array.isArray(value) ? value : [value]) form.append(key, item)
    }
    return request<T>(path, { method: 'POST', body: form })
  },
}
