"""Bootstrap del primer super-admin de plataforma.

Prende ``users.platform_admin`` para un email. Corre con la conexión PRIVILEGIADA
(``ALEMBIC_DATABASE_URL``, la misma de las migraciones — saltea RLS), porque el
usuario a promover puede estar en cualquier tenant. Se corre una sola vez:

    railway run python -m app.scripts.promote_platform_admin tu-email@ejemplo.com

Después, desde el panel de plataforma, un admin puede darle el flag a otros.
"""

from __future__ import annotations

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def _promote(email: str) -> int:
    url = os.environ.get("ALEMBIC_DATABASE_URL")
    if not url:
        print("ERROR: falta ALEMBIC_DATABASE_URL en el entorno.", file=sys.stderr)
        return -1
    engine = create_async_engine(url)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(
                text("UPDATE users SET platform_admin = true WHERE email = :email"),
                {"email": email},
            )
            return int(result.rowcount or 0)
    finally:
        await engine.dispose()


def main() -> None:
    if len(sys.argv) != 2:
        print("uso: python -m app.scripts.promote_platform_admin <email>", file=sys.stderr)
        raise SystemExit(2)
    email = sys.argv[1]
    promoted = asyncio.run(_promote(email))
    if promoted < 0:
        raise SystemExit(1)
    if promoted == 0:
        print(f"No se encontró ningún usuario con email {email!r} (¿ya se registró?).")
    else:
        print(f"OK: {promoted} usuario(s) con email {email!r} ahora son platform_admin.")


if __name__ == "__main__":
    main()
