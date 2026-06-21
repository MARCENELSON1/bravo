from __future__ import annotations

from app.domain.errors import DomainError


class ReservationNotFound(DomainError):
    code = "reservation_not_found"
    message = "No encontramos la reserva indicada."


class InvalidReservationTransition(DomainError):
    code = "invalid_reservation_transition"
    message = "No se puede cambiar el estado de la reserva de esta forma."


class InvalidPartySize(DomainError):
    code = "invalid_party_size"
    message = "La cantidad de personas debe ser mayor que cero."
