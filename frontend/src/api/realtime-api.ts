import type { HttpClient } from "@/api/http-client"
import { API_BASE_URL } from "@/lib/env"

export interface StreamTokenResponse {
  token: string
  expires_in: number
}

// Client for the realtime (SSE) layer. EventSource can't send an Authorization
// header, so we first fetch a short-lived, tenant-scoped token (Bearer-auth'd)
// and then ride it in the stream URL's query string.
export class RealtimeApi {
  private http: HttpClient

  constructor(http: HttpClient) {
    this.http = http
  }

  streamToken(): Promise<StreamTokenResponse> {
    return this.http.request<StreamTokenResponse>("POST", "/realtime/token", { auth: true })
  }

  kdsStreamUrl(token: string): string {
    return `${API_BASE_URL}/realtime/kds/stream?token=${encodeURIComponent(token)}`
  }
}
