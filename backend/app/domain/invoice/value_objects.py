from __future__ import annotations

from enum import StrEnum


class InvoiceType(StrEnum):
    """Comprobante. A: emisor RI → receptor RI (discrimina IVA). B: emisor RI →
    consumidor final/monotributo. C: emisor monotributo. NC/ND = ajustes.
    El mapeo a códigos AFIP (1/6/11, 3/8/13, 2/7/12) vive en el adapter."""

    FACTURA_A = "FACTURA_A"
    FACTURA_B = "FACTURA_B"
    FACTURA_C = "FACTURA_C"
    NOTA_CREDITO_A = "NOTA_CREDITO_A"
    NOTA_CREDITO_B = "NOTA_CREDITO_B"
    NOTA_CREDITO_C = "NOTA_CREDITO_C"
    NOTA_DEBITO_A = "NOTA_DEBITO_A"
    NOTA_DEBITO_B = "NOTA_DEBITO_B"
    NOTA_DEBITO_C = "NOTA_DEBITO_C"


class InvoiceStatus(StrEnum):
    DRAFT = "DRAFT"
    AUTHORIZED = "AUTHORIZED"  # con CAE
    REJECTED = "REJECTED"  # AFIP rechazó


class DocType(StrEnum):
    """Documento del receptor (códigos AFIP 80/86/96/99 en el adapter)."""

    CUIT = "CUIT"
    CUIL = "CUIL"
    DNI = "DNI"
    CONSUMIDOR_FINAL = "CONSUMIDOR_FINAL"


class Concept(StrEnum):
    PRODUCTOS = "PRODUCTOS"
    SERVICIOS = "SERVICIOS"
    AMBOS = "AMBOS"


class FiscalCondition(StrEnum):
    RESPONSABLE_INSCRIPTO = "RESPONSABLE_INSCRIPTO"
    MONOTRIBUTO = "MONOTRIBUTO"


# IVA en puntos básicos (sobre 10.000) → enteros exactos: 21% = 2100, 10.5% = 1050.
VAT_21 = 2100
VAT_105 = 1050
VAT_27 = 2700
VAT_0 = 0
