"""Datos que necesita el REPORTE DE USUARIO (clases simples del dominio de Control).

Reutiliza la entidad Prestamo y su regla `esta_vencido()` del contexto de Préstamos,
así la regla de "vencido" sigue definida en un solo lugar.
"""
from dataclasses import dataclass
from datetime import date

from backend.prestamos.domain.enums import EstadoPrestamo
from backend.prestamos.domain.Prestamo import Prestamo


@dataclass
class DatosUsuario:
    id: int
    nombre: str
    correo: str
    tipo: str
    estado: str
    credibilidad: float


@dataclass
class PrestamoDeUsuario:
    prestamo: Prestamo               # fechas y estado del préstamo
    equipo: str                      # qué se llevó
    estado_fisico: str | None        # cómo lo devolvió (None si aún no lo devuelve)
    obs_entrega: str                 # observaciones al entregarlo
    obs_devolucion: str              # observaciones al recibirlo

    def fecha_real(self) -> date | None:
        return self.prestamo.fecha_devolucion_real

    def situacion(self) -> str:
        p = self.prestamo
        if p.estado == EstadoPrestamo.DEVUELTO:
            tarde = p.fecha_devolucion_real and p.fecha_devolucion_real > p.fecha_devolucion_prevista
            return "Devuelto con retraso" if tarde else "Devuelto a tiempo"
        if p.estado == EstadoPrestamo.CANCELADO:
            return "Cancelado"
        return "Vencido" if p.esta_vencido() else "En plazo"


@dataclass
class ReservaDeUsuario:
    id: int
    equipo: str
    fecha_inicio: date
    fecha_fin: date
    estado: str
