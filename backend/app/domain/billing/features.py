"""Catálogo de capacidades que un plan puede incluir (los toggles del panel de
plataforma). Es la fuente de verdad de qué features existen; cada plan referencia
un subconjunto por su clave. El ENFORCEMENT (gatear features en la app) es un paso
aparte y parity-safe — acá solo se define y se edita el catálogo."""

from __future__ import annotations

# clave estable (guardada en el plan) → etiqueta legible (para el panel).
FEATURE_CATALOG: dict[str, str] = {
    "copilot": "Copiloto IA",
    "advisor": "Asesor financiero",
    "reports_export": "Exportar reportes al contador",
    "multi_location": "Multi-local",
    "crm": "CRM / clientes",
    "inventory": "Inventario y food cost",
}


def is_known_feature(key: str) -> bool:
    return key in FEATURE_CATALOG
