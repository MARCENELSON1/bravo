import { ApiError } from "@/api/api-error"
import {
  clearAccessToken,
  getAccessToken,
  notifyUnauthorized,
  setAccessToken,
} from "@/api/token-store"

export interface RequestOptions {
  // JSON body (serialized as application/json).
  body?: unknown
  // Form body (application/x-www-form-urlencoded) — used by the OAuth2 login.
  form?: URLSearchParams
  // Attach the Bearer access token and enable transparent refresh-on-401.
  auth?: boolean
  // Extra request headers (e.g. the presence display's X-Device-Token).
  headers?: Record<string, string>
  signal?: AbortSignal
}

// Port: every data client depends on this interface, never on fetch directly.
export interface HttpClient {
  request<T>(method: string, path: string, options?: RequestOptions): Promise<T>
}

const REFRESH_PATH = "/auth/refresh"

// Adapter over fetch. Responsibilities: attach the Bearer token, send the
// HttpOnly cookie (credentials: include), translate { code, message } into an
// ApiError, and transparently refresh the access token on a 401 (single-flight:
// concurrent 401s share ONE refresh call, then retry once).
export class FetchHttpClient implements HttpClient {
  private baseUrl: string
  private refreshing: Promise<boolean> | null = null

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  async request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
    let response = await this.send(method, path, options)

    if (response.status === 401 && options.auth && !path.startsWith(REFRESH_PATH)) {
      const refreshed = await this.tryRefresh()
      if (refreshed) {
        response = await this.send(method, path, options)
      }
    }

    return this.handle<T>(response)
  }

  private async send(method: string, path: string, options: RequestOptions): Promise<Response> {
    const headers: Record<string, string> = { Accept: "application/json" }
    let body: BodyInit | undefined

    if (options.form) {
      headers["Content-Type"] = "application/x-www-form-urlencoded"
      body = options.form.toString()
    } else if (options.body !== undefined) {
      headers["Content-Type"] = "application/json"
      body = JSON.stringify(options.body)
    }

    if (options.auth) {
      const token = getAccessToken()
      if (token) headers["Authorization"] = `Bearer ${token}`
    }

    if (options.headers) Object.assign(headers, options.headers)

    return fetch(this.baseUrl + path, {
      method,
      headers,
      body,
      // Send/receive the HttpOnly refresh cookie on the auth endpoints.
      credentials: "include",
      signal: options.signal,
    })
  }

  private async handle<T>(response: Response): Promise<T> {
    if (response.ok) {
      if (response.status === 204) return undefined as T
      const text = await response.text()
      return (text ? JSON.parse(text) : undefined) as T
    }

    let code = "unknown"
    let message = "Ocurrió un error inesperado."
    try {
      const data: unknown = await response.json()
      if (data && typeof data === "object") {
        const record = data as Record<string, unknown>
        if (typeof record.code === "string") code = record.code
        if (typeof record.message === "string") message = record.message
      }
    } catch {
      // Non-JSON error body (e.g. a proxy 502) — keep the generic message.
    }
    throw new ApiError(code, message, response.status)
  }

  // Single-flight refresh against the HttpOnly cookie. Returns whether a fresh
  // access token was obtained; on failure it tears the session down.
  private tryRefresh(): Promise<boolean> {
    this.refreshing ??= this.performRefresh()
    return this.refreshing
  }

  private async performRefresh(): Promise<boolean> {
    try {
      const response = await this.send("POST", REFRESH_PATH, {})
      if (!response.ok) {
        clearAccessToken()
        notifyUnauthorized()
        return false
      }
      const data = (await response.json()) as { access_token: string }
      setAccessToken(data.access_token)
      return true
    } catch {
      clearAccessToken()
      notifyUnauthorized()
      return false
    } finally {
      this.refreshing = null
    }
  }
}
