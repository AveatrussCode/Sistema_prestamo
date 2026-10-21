class DomainError(Exception):
    """Error de regla de negocio (400 en la API)."""


class ConflictError(Exception):
    """Conflicto de estado: el recurso ya existe o ya está ocupado (409 en la API)."""


class NotFoundError(Exception):
    """Recurso no encontrado (404 en la API)."""