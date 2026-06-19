from app.domain.errors import DomainError


class InvalidToken(DomainError):
    code = "invalid_token"
    message = "El enlace no es válido."


class ExpiredToken(DomainError):
    code = "expired_token"
    message = "El enlace expiró. Pedí uno nuevo."


class TokenAlreadyUsed(DomainError):
    code = "token_already_used"
    message = "Este enlace ya fue utilizado."


class InvalidInvitation(DomainError):
    code = "invalid_invitation"
    message = "La invitación no es válida o expiró."
