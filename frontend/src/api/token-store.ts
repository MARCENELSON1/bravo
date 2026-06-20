// The access token lives ONLY in memory (never localStorage/sessionStorage) so
// it is not reachable by persistent XSS. The refresh token is never stored here
// at all: it travels in an HttpOnly cookie the JS cannot read. A reload restores
// the session via a silent refresh against that cookie.

let accessToken: string | null = null
let unauthorizedHandler: (() => void) | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function clearAccessToken(): void {
  accessToken = null
}

// The AuthProvider registers a handler so a failed refresh tears the session
// down (→ redirect to /login) without the data layer importing React.
export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler
}

export function notifyUnauthorized(): void {
  unauthorizedHandler?.()
}
