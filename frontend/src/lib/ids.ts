// Client-generated ids. Generating the id on the client makes the create/add
// idempotent on the server (a retry or offline replay with the same id is a
// no-op) AND lets optimistic UI use the *final* id immediately — so when the
// server response comes back there is no reconciliation flicker or duplicate.
export function newId(): string {
  return crypto.randomUUID()
}
