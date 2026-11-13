"""PUERTO (interfaz) para obtener los pendientes de devolución.

El dominio y la aplicación solo conocen ESTA interfaz. Quién la implementa
(SQL, otra base, datos falsos en una prueba) lo decide la infraestructura.
"""
from abc import ABC, abstractmethod

from backend.control.domain.pendiente_devolucion import PendienteDevolucion


class PendienteDevolucionRepository(ABC):

    @abstractmethod
    def listar_activos(self) -> list[PendienteDevolucion]:
        """Préstamos ACTIVOS (equipo sin devolver), con los datos del usuario y del equipo."""
