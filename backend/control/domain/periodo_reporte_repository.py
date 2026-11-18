"""PUERTO (interfaz) para obtener la actividad del sistema en un periodo (reporte mensual / por fechas).

Todas las fechas son inclusivas: un movimiento del día `hasta` SÍ entra en el reporte.
"""
from abc import ABC, abstractmethod
from datetime import date

from backend.control.domain.registro_prestamo import RegistroPrestamo, RegistroReserva


class PeriodoReporteRepository(ABC):

    @abstractmethod
    def prestamos_entregados(self, desde: date, hasta: date) -> list[RegistroPrestamo]:
        """Préstamos cuya entrega (fecha de inicio) cae dentro del periodo, del más antiguo al más reciente."""

    @abstractmethod
    def devoluciones(self, desde: date, hasta: date) -> list[RegistroPrestamo]:
        """Préstamos devueltos dentro del periodo, de la devolución más antigua a la más reciente."""

    @abstractmethod
    def reservas(self, desde: date, hasta: date) -> list[RegistroReserva]:
        """Reservas hechas (fecha de reserva) dentro del periodo, de la más antigua a la más reciente."""
