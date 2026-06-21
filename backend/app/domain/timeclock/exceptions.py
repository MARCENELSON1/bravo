from __future__ import annotations

from app.domain.errors import DomainError


class ShiftAlreadyOpen(DomainError):
    code = "shift_already_open"
    message = "Ya tenés un turno abierto. Fichá la salida antes de marcar otra entrada."


class NoOpenShift(DomainError):
    code = "no_open_shift"
    message = "No tenés ningún turno abierto para fichar la salida."


class ShiftNotFound(DomainError):
    code = "shift_not_found"
    message = "No encontramos el turno indicado."


class ShiftAlreadyClosed(DomainError):
    code = "shift_already_closed"
    message = "El turno ya está cerrado."


class InvalidShiftTime(DomainError):
    code = "invalid_shift_time"
    message = "La hora de salida no puede ser anterior a la de entrada."
