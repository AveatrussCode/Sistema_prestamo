from abc import ABC, abstractmethod
from datetime import date
from typing import Optional

from backend.prestamos.domain.reserva import EstadoReserva, Reserva


class ReservaRepository(ABC):

    @abstractmethod
    def guardar(self, reserva: Reserva) -> Reserva:
        """Inserta si id_reserva es None; si no, actualiza."""

    @abstractmethod
    def buscar_por_id(self, id_reserva: int) -> Optional[Reserva]: ...

    @abstractmethod
    def listar(self, usuario_id: Optional[int] = None, objeto_id: Optional[int] = None,
               estado: Optional[EstadoReserva] = None) -> list[Reserva]: ...

    @abstractmethod
    def existe_solapada(self, objeto_id: int, fecha_inicio: date, fecha_fin: date,
                        excluir_id: Optional[int] = None) -> bool:
        """True si ya hay una reserva ACTIVA de ese objeto que se cruza con [inicio, fin]."""
