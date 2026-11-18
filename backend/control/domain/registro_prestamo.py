"""Datos que comparten el REPORTE DE EQUIPO y el REPORTE POR PERIODO (clases simples del dominio de Control).

Reutiliza la entidad Prestamo y su regla `esta_vencido()` del contexto de Préstamos,
así la regla de "vencido" sigue definida en un solo lugar.
"""
from dataclasses import dataclass
from datetime import date

from backend.prestamos.domain.enums import EstadoPrestamo
from backend.prestamos.domain.Prestamo import Prestamo


@dataclass
class DatosEquipo:
    id: int
    nombre: str
    descripcion: str
    categoria: str
    disponibilidad: str   # valor crudo: DISPONIBLE, PRESTADO, RESERVADO, NO_DISPONIBLE, DADO_DE_BAJA
    estado_fisico: str    # valor crudo: BUENO, REGULAR, DANHADO


@dataclass
class RegistroPrestamo:
    """Un préstamo con quién lo tuvo, qué equipo fue y cómo se devolvió."""
    prestamo: Prestamo               # fechas y estado del préstamo
    usuario: str                     # quién lo tuvo
    correo: str | None               # None si el usuario fue eliminado
    equipo: str                      # qué se llevó
    estado_fisico: str | None        # cómo se devolvió (None si aún no se devuelve)
    obs_entrega: str                 # observaciones al entregarlo
    obs_devolucion: str              # observaciones al recibirlo

    def fecha_real(self) -> date | None:
        return self.prestamo.fecha_devolucion_real

    def devuelto_con_retraso(self) -> bool:
        p = self.prestamo
        return (
            p.estado == EstadoPrestamo.DEVUELTO
            and p.fecha_devolucion_real is not None
            and p.fecha_devolucion_real > p.fecha_devolucion_prevista
        )

    def situacion(self) -> str:
        p = self.prestamo
        if p.estado == EstadoPrestamo.DEVUELTO:
            return "Devuelto con retraso" if self.devuelto_con_retraso() else "Devuelto a tiempo"
        if p.estado == EstadoPrestamo.CANCELADO:
            return "Cancelado"
        return "Vencido" if p.esta_vencido() else "En plazo"

    def dias_en_poder(self) -> int | None:
        """Días que el equipo estuvo (o lleva) en manos de la persona. None si el préstamo se canceló."""
        p = self.prestamo
        if p.estado == EstadoPrestamo.CANCELADO:
            return None
        devuelto = p.estado == EstadoPrestamo.DEVUELTO and p.fecha_devolucion_real
        fin = p.fecha_devolucion_real if devuelto else date.today()
        return max((fin - p.fecha_inicio).days, 0)


@dataclass
class RegistroReserva:
    id: int
    usuario: str          # "(usuario eliminado)" si ya no existe
    equipo: str           # "(equipo eliminado)" si ya no existe
    fecha_reserva: date   # cuándo se hizo la reserva
    fecha_inicio: date
    fecha_fin: date
    estado: str           # valor crudo: PENDIENTE, CONFIRMADA, FINALIZADA, CANCELADA, VENCIDA
