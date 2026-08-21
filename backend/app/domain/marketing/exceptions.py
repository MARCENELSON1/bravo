from app.domain.errors import DomainError


class InvalidLead(DomainError):
    code = "invalid_lead"
    message = "Revisá el email ingresado."


class LeadNotDelivered(DomainError):
    """El lead no llegó a destino. Se informa al visitante en vez de fingir
    éxito: un lead perdido en silencio es peor que un error visible."""

    code = "lead_not_delivered"
    message = "No pudimos registrar tus datos. Probá de nuevo en un momento."
