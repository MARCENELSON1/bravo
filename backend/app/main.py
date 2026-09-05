"""FastAPI application factory: lifespan, routers, error handlers, DI wiring."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.container import Container
from app.presentation.api.v1 import (
    advisor,
    analytics,
    auth,
    billing,
    cashier,
    copilot,
    customers,
    devices,
    expenses,
    finance,
    floor,
    integrations,
    inventory,
    invoices,
    kds,
    leads,
    me,
    orders,
    payments,
    ping,
    platform,
    products,
    public,
    public_menu,
    realtime,
    reports,
    reservations,
    sectors,
    self_order,
    self_pay,
    tables,
    tax,
    taxjar,
    tenants,
    timeclock,
    users,
    webhooks,
)
from app.presentation.errors import register_error_handlers


def create_app() -> FastAPI:
    container = Container()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        await container.db().dispose()
        # Releases the shared outbound connection pool; adapters never close it
        # themselves, since they share it for the life of the process.
        await container.http_pool().aclose()

    app = FastAPI(title="BRAVO API", version="0.1.0", lifespan=lifespan)
    app.state.container = container

    # CORS for split-domain deploys (SPA and API on different origins). With no
    # origins configured (dev), the SPA is same-origin via the Vite proxy.
    origins = [o.strip() for o in container.config().cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_error_handlers(app)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(billing.router, prefix="/api/v1")
    app.include_router(tenants.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(ping.router, prefix="/api/v1")
    app.include_router(me.router, prefix="/api/v1")
    app.include_router(devices.router, prefix="/api/v1")
    app.include_router(tables.router, prefix="/api/v1")
    app.include_router(sectors.router, prefix="/api/v1")
    app.include_router(customers.router, prefix="/api/v1")
    app.include_router(products.router, prefix="/api/v1")
    app.include_router(orders.router, prefix="/api/v1")
    app.include_router(kds.router, prefix="/api/v1")
    app.include_router(realtime.router, prefix="/api/v1")
    app.include_router(floor.router, prefix="/api/v1")
    app.include_router(payments.router, prefix="/api/v1")
    app.include_router(cashier.router, prefix="/api/v1")
    app.include_router(expenses.router, prefix="/api/v1")
    app.include_router(webhooks.router, prefix="/api/v1")
    app.include_router(integrations.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    app.include_router(invoices.router, prefix="/api/v1")
    app.include_router(tax.router, prefix="/api/v1")
    app.include_router(taxjar.router, prefix="/api/v1")
    app.include_router(platform.router, prefix="/api/v1")
    app.include_router(timeclock.router, prefix="/api/v1")
    app.include_router(inventory.router, prefix="/api/v1")
    app.include_router(reservations.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(advisor.router, prefix="/api/v1")
    app.include_router(finance.router, prefix="/api/v1")
    app.include_router(copilot.router, prefix="/api/v1")
    app.include_router(leads.router, prefix="/api/v1")
    app.include_router(public.router, prefix="/api/v1")
    app.include_router(public_menu.router, prefix="/api/v1")
    app.include_router(self_order.router, prefix="/api/v1")
    app.include_router(self_pay.router, prefix="/api/v1")

    @app.middleware("http")
    async def security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    _configure_logging()
    container.wire()
    return app


def _configure_logging() -> None:
    """Uvicorn solo configura sus propios loggers: sin esto, todo lo que la app
    emite a INFO se descarta en silencio (el rastro de los leads, el transporte
    de email de consola). Se engancha al handler de uvicorn para no duplicar."""
    app_logger = logging.getLogger("app")
    if app_logger.handlers:
        return
    app_logger.setLevel(logging.INFO)
    uvicorn_handlers = logging.getLogger("uvicorn").handlers
    app_logger.handlers = list(uvicorn_handlers) if uvicorn_handlers else [logging.StreamHandler()]
    app_logger.propagate = False


app = create_app()
