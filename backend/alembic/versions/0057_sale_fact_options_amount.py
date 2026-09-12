"""sale_facts.options_amount — separar el precio de carta de los adicionales.

El precio unitario de una línea trae los adicionales ya sumados: una milanesa de
$8.000 con panceta de $1.200 se registra a $9.200. Es una decisión buena para el
cálculo —toda la matemática posterior lee un solo número— pero deja el reporte de
rentabilidad sin poder comparar: el mismo plato aparece con precios distintos
según lo que cada comensal le agregó, el promedio no es el de la carta y lo que
factura el local por adicionales (margen alto) no se puede medir como línea.

Esta columna congela cuánto de ese unitario eran adicionales. El precio de carta
es ``unit_price_amount - options_amount``.

**No cambia ningún número existente.** Default 0, así que las filas previas y los
platos sin opciones se leen como "todo precio de carta", que es lo que son. Nada
la suma a ningún agregado: es dato de atribución, no de plata nueva.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0057_sale_fact_options_amount"
down_revision: str | None = "0056_outbox_tasks"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "sale_facts",
        sa.Column("options_amount", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("sale_facts", "options_amount")
