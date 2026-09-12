"""El aviso de "algo cambió en el plano", en un solo lugar.

Vive acá y no en ``order.use_cases`` porque lo publican **dos** flujos: el de
comandas (abrir, marchar, mover, servir) y el de cobro (la mesa que se libera al
saldar la última orden). Tenerlo duplicado sería tener dos definiciones del mismo
evento, que es exactamente cómo una termina desincronizada de la otra.
"""

from __future__ import annotations

from app.domain.realtime.ports import DomainEvent


def floor_changed(tenant_id: str, table_id: str | None) -> DomainEvent:
    """Señal de "volvé a pedir el plano": cambió la ocupación o el total de una mesa.

    Como todo evento del stream, no lleva los datos — solo el id de la mesa. El
    cliente los relee por el endpoint normal, con su filtro por tenant.
    """
    return DomainEvent(
        type="floor.changed",
        tenant_id=tenant_id,
        payload={"table_id": table_id},
    )
