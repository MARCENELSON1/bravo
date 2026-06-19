from app.domain.errors import DomainError


class InvalidEmail(DomainError):
    code = "invalid_email"
    message = "El email no tiene un formato válido."


class InvalidCredentials(DomainError):
    code = "invalid_credentials"
    message = "Email o contraseña incorrectos."


class UserLocked(DomainError):
    code = "user_locked"
    message = "La cuenta está bloqueada temporalmente por intentos fallidos. Probá más tarde."


class EmailNotVerified(DomainError):
    code = "email_not_verified"
    message = "Tenés que verificar tu email antes de ingresar."


class InactiveUser(DomainError):
    code = "inactive_user"
    message = "La cuenta no está activa."


class UserNotFound(DomainError):
    code = "user_not_found"
    message = "No encontramos al usuario."


class InsufficientRole(DomainError):
    code = "insufficient_role"
    message = "No tenés permisos para realizar esta acción."


class EmailAlreadyRegistered(DomainError):
    code = "email_already_registered"
    message = "Ya existe una cuenta con ese email."
