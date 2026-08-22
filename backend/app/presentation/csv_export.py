from __future__ import annotations

import csv
import io

from fastapi import Response

from app.application.reporting.exports import ExportTable

# Byte-order mark so Excel-AR opens the UTF-8 file with acentos intact.
_BOM = chr(0xFEFF)


def to_csv(table: ExportTable) -> str:
    """Serialize a table as CSV apt for Excel-AR: ``;`` delimiter + CRLF, with the
    stdlib quoting (fields with ``;``/``"``/newline get quoted, ``"`` doubled)."""
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", lineterminator="\r\n")
    writer.writerow(table.headers)
    writer.writerows(table.rows)
    return buf.getvalue()


def csv_response(filename: str, table: ExportTable) -> Response:
    """A downloadable CSV response (UTF-8 with BOM so Excel-AR reads the acentos)."""
    body = _BOM + to_csv(table)
    return Response(
        content=body.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
