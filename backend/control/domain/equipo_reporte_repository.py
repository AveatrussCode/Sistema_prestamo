"""PUERTO (interfaz) para obtener los datos del reporte de un equipo.

La aplicación solo conoce ESTA interfaz; quién la implementa (SQL, etc.) lo decide la infraestructura.
"""
from abc import ABC, abstractmethod

from backend.control.domain.registro_prestamo import DatosEquipo, RegistroPrestamo, RegistroReserva


class EquipoReporteRepository(ABC):

    @abstractmethod
    def datos_de(self, id_equipo: int) -> DatosEquipo | None:
        """Datos básicos del equipo, o None si no existe."""

    @abstractmethod
    def prestamos_de(self, id_equipo: int) -> list[RegistroPrestamo]:
        """Todos los préstamos del equipo, del más reciente al más antiguo."""

    @abstractmethod
    def reservas_de(self, id_equipo: int) -> list[RegistroReserva]:
        """Todas las reservas del equipo, de la más reciente a la más antigua."""
