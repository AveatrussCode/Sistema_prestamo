from abc import ABC, abstractmethod


class UsuarioLookup(ABC):
    """Puerto para consultar usuarios desde el contexto de préstamos."""

    @abstractmethod
    def existe(self, usuario_id: int) -> bool: ...

    @abstractmethod
    def esta_activo(self, usuario_id: int) -> bool: ...


class ObjetoLookup(ABC):
    """Puerto para consultar objetos desde el contexto de préstamos."""

    @abstractmethod
    def existe(self, objeto_id: int) -> bool: ...

    @abstractmethod
    def esta_disponible(self, objeto_id: int) -> bool: ...

    @abstractmethod
    def marcar_reservado(self, objeto_id: int) -> None: ...

    @abstractmethod
    def marcar_disponible(self, objeto_id: int) -> None: ...