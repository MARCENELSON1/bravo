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

## Running more than one replica

The app defaults to in-process cache, event bus and rate limiter. That is correct
for a single worker and needs no extra infrastructure, but it does **not** survive
horizontal scaling: each replica would keep its own catalog cache (an invalidation
on one is invisible to the others), a waiter's SSE stream would miss what another
replica published, and the abuse limit on the public QR endpoints would be
enforced N times over instead of once.

Before raising the replica count, move all three onto Redis:

| Variable | Value | Without it, when scaled |
| --- | --- | --- |
| `REDIS_URL` | `redis://…` (Railway's Redis service URL) | — |
| `CACHE_BACKEND` | `redis` | Stale products/menu after an edit, per replica |
| `EVENT_BUS_BACKEND` | `redis` | KDS/floor updates only reach the publishing replica |
| `RATE_LIMITER_BACKEND` | `redis` | The public rate limit multiplies by replica count |

`REDIS_URL` has **no default on purpose**: the three adapters fail open, so a
default pointing at localhost would boot a healthy-looking process with no cache,
no cross-replica events and no rate limit, silently. Setting any of the three to
`redis` without a URL fails at startup instead.

Redis is a **nudge and a cache, never the source of truth** — Postgres is. A Redis
outage degrades the system (cache always misses, realtime falls back to the
client's poll, the abuse guard opens) but never takes it down or loses data.

## Multi-tenant & RLS

- The app connects with a dedicated **non-superuser** role (`bravo_app`).
- Tenant-scoped tables `ENABLE` + `FORCE ROW LEVEL SECURITY`.
- Every request runs inside a transaction with `SET LOCAL app.tenant_id = '<uuid>'`;
  policies use `current_setting('app.tenant_id')::uuid`.
- Repositories also filter by `tenant_id` explicitly (defence in depth).
