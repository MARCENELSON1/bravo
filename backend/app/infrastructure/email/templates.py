"""Transactional email content in Spanish (UX). Returns (subject, body)."""

from __future__ import annotations

_SIGNATURE = "— El equipo de BRAVO"


def verification_email(link: str) -> tuple[str, str]:
    subject = "Verificá tu email — BRAVO"
    body = (
        "¡Hola!\n\n"
        "Gracias por crear tu cuenta en BRAVO. Para activarla, verificá tu email "
        "haciendo clic en el siguiente enlace:\n\n"
        f"{link}\n\n"
        "Si no fuiste vos, podés ignorar este mensaje.\n\n"
        f"{_SIGNATURE}"
    )
    return subject, body


def password_reset_email(link: str) -> tuple[str, str]:
    subject = "Restablecé tu contraseña — BRAVO"
    body = (
        "Recibimos un pedido para restablecer tu contraseña.\n\n"
        "Creá una nueva contraseña desde este enlace "
        "(vence pronto y se puede usar una sola vez):\n\n"
        f"{link}\n\n"
        "Si no lo pediste, ignorá este mensaje: tu contraseña no cambió.\n\n"
        f"{_SIGNATURE}"
    )
    return subject, body


def invitation_email(link: str, tenant_name: str) -> tuple[str, str]:
    subject = f"Te invitaron a {tenant_name} en BRAVO"
    body = (
        f"Te sumaron al equipo de {tenant_name} en BRAVO.\n\n"
        "Aceptá la invitación y definí tu contraseña desde este enlace:\n\n"
        f"{link}\n\n"
        "Si no esperabas esta invitación, podés ignorar este mensaje.\n\n"
        f"{_SIGNATURE}"
    )
    return subject, body
