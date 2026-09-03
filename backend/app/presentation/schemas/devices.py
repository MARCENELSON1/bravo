from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RegisterDeviceRequest(BaseModel):
    # FCM registration token del device + plataforma (para el push, Fase 4).
    token: str
    platform: Literal["ios", "android"]
