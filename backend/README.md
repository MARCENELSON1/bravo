# BRAVO — Backend

FastAPI backend built with **Clean Architecture + Ports & Adapters + DI container**.
Multi-tenant (per-tenant filtering + Postgres RLS) with a complete identity/login subsystem.

> Language convention: **all backend code in English** (classes, functions, endpoints,
> DB tables/columns). **UX in Spanish** (email content, user-facing error `message`).
> API errors return an English `code` + a Spanish `message`.

## Layers

```
app/
├─ domain/          # pure Python: entities, value objects, exceptions, ports (ABCs)
├─ application/     # use cases — depend on domain ports only
├─ infrastructure/  # adapters: persistence (SQLAlchemy), security, email
├─ presentation/    # FastAPI routers (thin), schemas, deps, errors, rbac
├─ container.py     # dependency-injector wiring (ports → adapters)
├─ config.py        # pydantic-settings
└─ main.py          # app factory + lifespan + wiring
```

## Setup

```bash
cd backend
poetry install
cp .env.example .env          # then edit secrets / DB URLs

# Create the non-superuser app role + schema + RLS policies
poetry run alembic upgrade head

# Run
poetry run uvicorn app.main:app --reload   # http://localhost:8000/docs
```

## Validation

```bash
poetry run ruff check .
poetry run mypy app
poetry run pytest tests/unit -q --cov=app/domain --cov=app/application --cov-report=term-missing
poetry run pytest tests/integration -q
```

## Security notes

- **Production config is guarded**: outside `ENV=dev`, the app refuses to start with a
  default `JWT_SECRET`/`DATABASE_URL`, a non-HTTPS `APP_BASE_URL`, or `EMAIL_TRANSPORT=console`.
- **Token storage (frontend)**: the API returns `access_token` + `refresh_token` in the JSON
  body. Prefer keeping them in memory; if persisted, treat them as secrets. Avoid
  `localStorage` on shared/tablet devices (XSS risk) — a future iteration may move refresh
  tokens to `HttpOnly`/`Secure`/`SameSite` cookies.
- **Rate limiting**: v1 relies on per-user DB lockout; per-IP throttling (and HTTPS/HSTS at
  the reverse proxy) are deployment follow-ups.

## Multi-tenant & RLS

- The app connects with a dedicated **non-superuser** role (`bravo_app`).
- Tenant-scoped tables `ENABLE` + `FORCE ROW LEVEL SECURITY`.
- Every request runs inside a transaction with `SET LOCAL app.tenant_id = '<uuid>'`;
  policies use `current_setting('app.tenant_id')::uuid`.
- Repositories also filter by `tenant_id` explicitly (defence in depth).
