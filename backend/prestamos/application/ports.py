from abc import ABC, abstractmethod


class UsuarioLookup(ABC):
    """Puerto para consultar usuarios desde el contexto de préstamos."""

    @abstractmethod
    def existe(self, usuario_id: int) -> bool: ...

    @abstractmethod
    def esta_activo(self, usuario_id: int) -> bool: ...

class CredibilidadPort(ABC):
    """Puerto: lo que Reservas necesita del sistema de credibilidad (lo implementa el contexto Control)."""

    @abstractmethod
    def validar_reserva(self, usuario_id: int, fecha_inicio, fecha_fin, hoy) -> None: ...

    @abstractmethod
    def sancionar_no_recogida(self, usuario_id: int, reserva_id: int) -> None: ...

    @abstractmethod
    def sancionar_cancelacion_tardia(self, usuario_id: int, reserva_id: int) -> None: ...
