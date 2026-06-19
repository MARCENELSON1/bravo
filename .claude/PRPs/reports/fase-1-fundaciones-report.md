# Implementation Report: Fase 1 — Fundaciones + Identidad/Login

## Summary
Built the BRAVO backend skeleton with **Clean Architecture + Ports & Adapters + DI
container**, **multi-tenant Postgres with RLS**, and a **complete, secure identity/login
subsystem** (JWT access + rotating opaque refresh, Argon2 hashing, email verification,
password reset via email, tenant onboarding, staff invitations, RBAC, lockout, and an
auth audit log). All backend code/identifiers are in English; user-facing copy (emails,
error `message`) is in Spanish, with errors returning `{code (EN), message (ES)}`.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | XL | XL (delivered in milestones M0–M6) |
| Confidence | 7/10 single-pass | Completed in one pass; all validations green |
| Files Changed | ~45–55 new | ~80 new files (68 `app/` modules + 11 test files + tooling/alembic) |
| Coverage (domain+application) | ≥80% | **97%** |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | Bootstrap (Poetry + layers) | ✅ | Pinned venv to Python 3.12 (was 3.14); added explicit `greenlet` |
| 2 | Settings + `.env.example` | ✅ | Added `email_transport`, `invitation_token_ttl_hours` |
| 3 | Async Database + SET LOCAL tenant | ✅ | `set_config('app.tenant_id', :v, true)` (parameterized) |
| 4 | ORM models + mappers | ✅ | `Uuid(as_uuid=False)`; `*_to_orm` omits `created_at` |
| 5 | Alembic async migration + RLS | ✅ | `bravo_app` role + FORCE RLS; downgrade/upgrade verified |
| 6 | Domain (entities, VOs, ports) | ✅ | Added `TenantContext` port; `InsufficientRole` error |
| 7 | Auth core use cases | ✅ | Refresh use case named `RefreshAccessToken` (see Deviations) |
| 8 | Recovery/verify/invite use cases | ✅ | Neutral forgot-password; single-use hashed tokens |
| 9 | Infra adapters + repos | ✅ | Argon2, JWT, SMTP + Console email, 7 SQLAlchemy repos |
| 10 | Presentation (deps/rbac/errors/routers/schemas) | ✅ | 11 endpoints; domain→HTTP mapping in `errors.py` |
| 11 | DI container + `main.py` | ✅ | `Selector` for email transport; lifespan disposes engine |
| 12 | Test suite + coverage | ✅ | 50 tests (41 unit, 9 integration/e2e), 97% coverage |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis (ruff) | ✅ Pass | `ruff check .` clean |
| Static Analysis (mypy) | ✅ Pass | 68 source files, 0 issues |
| Unit Tests | ✅ Pass | 41 tests; coverage 97% (domain+application) |
| Integration / E2E | ✅ Pass | 9 tests (RLS isolation + full HTTP flows) |
| Build / Migrations | ✅ Pass | `alembic upgrade/downgrade` round-trip; RLS policies present |
| Dev server | ✅ Pass | `/health` ok, `/docs` 200, OpenAPI 12 paths |
| RLS isolation | ✅ Pass | Tenant A cannot see Tenant B's rows as `bravo_app`; no-context → 0 rows |

## Key Design Decisions
- **Tenant slug**: `Tenant` has a unique `slug`; login & forgot-password carry it (emails
  are unique per-tenant, so auth needs a tenant discriminator). Login uses the OAuth2
  password flow with the slug in the form `client_id`.
- **Opaque tokens are `"{tenant_id}.{secret}"`**: refresh/reset/verify/invitation flows
  derive their tenant from the token (no JWT yet) and establish RLS scope. Only the
  SHA-256 hash is stored; tokens are single-use (reset/verify/invite) or rotated (refresh).
- **`TenantContext` port**: unauthenticated token flows set RLS scope cleanly via a port,
  keeping `app.context` out of the application layer.
- **RLS scope**: `users` and `auth_audit` get `FORCE ROW LEVEL SECURITY` + isolation
  policy. Token tables carry `tenant_id` and are filtered explicitly, but are looked up by
  their unique high-entropy hash (the capability) outside a tenant session, so they are
  intentionally not RLS-gated (documented in the migration).

## Deviations from Plan
1. **Build order**: wrote the domain layer (T6) before ORM mappers (T4) because mappers
   depend on domain entities. Models written in T4 as planned; mappers right after domain.
2. **Refresh use-case name**: `RefreshAccessToken` instead of `RefreshToken` to avoid
   shadowing the domain `RefreshToken` token model.
3. **Console email transport**: added a `ConsoleEmailSender` (selected via
   `EMAIL_TRANSPORT=console`) for local dev since no MailHog is running; SMTP adapter
   remains the prod path behind the same port.
4. **Extra settings**: `email_transport`, `invitation_token_ttl_hours`,
   `ALEMBIC_DATABASE_URL` (admin URL for migrations vs the non-superuser app URL).

## Issues Encountered
- **Poetry built the venv with Python 3.14** (system default) → switched with
  `poetry env use python3.12`.
- **greenlet missing** (SQLAlchemy async) on macOS arm64 — its marker checks `aarch64`,
  not `arm64`; declared `greenlet` explicitly in `pyproject.toml`.
- **ruff B008** flagged FastAPI `Depends()` in arg defaults — added a per-file ignore for
  `app/presentation/**` (the DI idiom requires calls in defaults).

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `tests/unit/test_domain.py` | 9 | Email VO, lockout, `can_login` states |
| `tests/unit/test_config.py` | 2 | Settings from env/defaults |
| `tests/unit/test_auth_core.py` | 14 | login/refresh/logout/change-password |
| `tests/unit/test_recovery_invitations.py` | 16 | reset/verify/onboard/invite/accept |
| `tests/integration/test_rls.py` | 2 | RLS isolation between tenants |
| `tests/integration/test_e2e_auth.py` | 7 | full HTTP flows, RBAC, neutrality |

## Security Remediation (post `security-reviewer`)

Ran `ecc:security-reviewer` over the identity subsystem. Findings triaged and
remediated in-scope; the rest deferred with justification.

**Fixed (all validations still green: ruff, mypy, 52 tests, 97% coverage):**
- **C-1** — `Settings` now fails fast (`@model_validator`) outside `env=dev` if the JWT
  secret is the default, `DATABASE_URL` is the default, `APP_BASE_URL` isn't HTTPS, or
  `EMAIL_TRANSPORT=console` (which would log token links). Covers L-1/L-3/L-6 too.
- **M-1** — Token flows (refresh/reset/verify/accept/logout) now set the RLS tenant from
  the **authoritative DB record**, not the untrusted token prefix (prefix still validated
  early for fast rejection).
- **M-2** — Access JWTs carry `iss`/`aud` and `decode` requires `exp`/`iat`/`sub`/`type`.
- **M-3** — Invitation privilege ceiling: a role may only invite roles strictly below it
  (MANAGER can no longer invite a peer MANAGER).
- **M-4** — `ChangePassword` revalidates `can_login()` (defence in depth).
- **H-4** — `RequestPasswordReset` invalidates outstanding reset tokens before issuing a
  new one (only the newest link is valid).
- **L-2** — `jwt_alg` constrained to an `HS*` allowlist (`Literal`).
- **L-4** — `smtp_use_tls` now defaults to `true`.
- Added baseline security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`).

**Deferred (documented):**
- **H-1 (rate limiting)** — the plan explicitly scopes v1 to DB lockout (Redis later); the
  per-user lockout is in place. Per-IP throttling is a follow-up.
- **H-2 (login reveals `email_not_verified`/`inactive`)** — **Decision (owner, 2026-06-18):
  keep the explicit "verificá tu email" message** over strict anti-enumeration. Rationale:
  onboarding clarity beats the small, lockout-mitigated enumeration risk; the e2e test pins
  this behaviour. Re-evaluate once per-IP rate limiting lands (which largely neutralizes the
  residual risk).
- **H-3 (HTTPS redirect/HSTS)** — belongs at the reverse proxy; the prod config guard now
  requires an HTTPS `APP_BASE_URL`.
- **M-5/M-6 (token storage)** — frontend concern; documented in `backend/README.md`.

## Next Steps
- [ ] Code review via `/code-review`.
- [ ] Frontend login screens (consumes these endpoints) — future phase.
- [ ] Commit via `/prp-commit`, PR via `/prp-pr`.
