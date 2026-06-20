// Uniform API error: the backend returns { code, message } where `code` is a
// stable English string (e.g. "invalid_credentials") and `message` is a
// Spanish, user-facing text. Screens branch on `code` and display `message`.
export class ApiError extends Error {
  code: string
  status: number

  constructor(code: string, message: string, status: number) {
    super(message)
    this.name = "ApiError"
    this.code = code
    this.status = status
  }
}

export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError
}
