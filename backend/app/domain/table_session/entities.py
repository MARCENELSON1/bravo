from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.table_session.value_objects import SessionOrigin, SessionStatus


@dataclass
class Sector:
    """Zona del salón (salón/terraza/barra/vereda) para agrupar mesas y facturar por
    sector. `sort_order`/`color` para el tablero."""

    id: str
    tenant_id: str
    name: str
    color: str | None = None
    sort_order: int = 0
    created_at: datetime | None = None


@dataclass
class TableSession:
    """La VISITA de una mesa como unidad de negocio (turno de mesa), separada de la
    comanda (que es el contenedor de ítems). Posee el ciclo de vida: cuándo se
    sentaron, cuántos son (pax), qué mozo, y los timestamps que alimentan los timers
    y el estado del floor. Inmutable una vez cerrada. Las comandas cuelgan de la
    sesión vía `orders.session_id` (1:N)."""

    id: str
    tenant_id: str
    table_id: str
    status: SessionStatus = SessionStatus.OPEN  # cache; el vivo es derivado
    origin: SessionOrigin = SessionOrigin.SALON
    pax: int | None = None
    waiter_id: str | None = None
    opened_at: datetime | None = None
    first_item_at: datetime | None = None
    fired_at: datetime | None = None
    ready_at: datetime | None = None
    bill_requested_at: datetime | None = None
    closed_at: datetime | None = None
    merged_into_id: str | None = None
    customer_id: str | None = None
    notes: str | None = None

    def close(self, now: datetime) -> None:
        """The visit is over (last order paid / cancelled, or staff closed the
        table): sealed as CLOSED so the floor shows the table free again."""
        self.status = SessionStatus.CLOSED
        self.closed_at = now

    def assign_waiter(self, waiter_id: str) -> None:
        """Set (or change) the owner of the visit. Único punto de mutación del
        dueño tras abrir la sesión: lo usan confirmar-QR, tomar mesa y reasignar."""
        self.waiter_id = waiter_id
