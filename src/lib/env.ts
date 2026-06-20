// Base URL of the BRAVO API. In dev it is a relative path proxied by Vite to the
// FastAPI backend, so the SPA and API share an origin and the refresh cookie
// stays first-party. Override via VITE_API_URL.
export const API_BASE_URL: string = import.meta.env.VITE_API_URL ?? "/api/v1"
