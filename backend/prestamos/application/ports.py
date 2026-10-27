from abc import ABC, abstractmethod


class UsuarioLookup(ABC):
    """Puerto para consultar usuarios desde el contexto de préstamos."""

    @abstractmethod
    def existe(self, usuario_id: int) -> bool: ...

    @abstractmethod
    def esta_activo(self, usuario_id: int) -> bool: ...
