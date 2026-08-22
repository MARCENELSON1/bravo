"""Unit: CSV serializer for the accountant exports (quoting + delimiter)."""

from __future__ import annotations

from app.application.reporting.exports import ExportTable
from app.presentation.csv_export import csv_response, to_csv


def test_to_csv_uses_semicolon_and_crlf():
    table = ExportTable(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])
    out = to_csv(table)
    assert out == "A;B\r\n1;2\r\n3;4\r\n"


def test_to_csv_quotes_fields_with_delimiter_or_quotes():
    table = ExportTable(
        headers=["Detalle", "Monto"],
        rows=[['pago a "Juan"; contado', "1500,00"]],
    )
    out = to_csv(table)
    # El punto y coma y las comillas fuerzan comillas; las internas se duplican.
    assert '"pago a ""Juan""; contado";1500,00' in out


def test_csv_response_has_bom_and_download_headers():
    resp = csv_response("ventas.csv", ExportTable(headers=["A"], rows=[["1"]]))
    assert resp.body.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM
    assert resp.media_type == "text/csv; charset=utf-8"
    assert 'attachment; filename="ventas.csv"' in resp.headers["content-disposition"]
