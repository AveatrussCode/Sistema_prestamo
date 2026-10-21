
from dataclasses import dataclass
from datetime import date

from backend.prestamos.domain.enums import EstadoDeSolicitudPrestamo


@dataclass
class SolicitudPrestamo:
    id_solicitud: int
    fecha_solicitud: date
    estado: EstadoDeSolicitudPrestamo
    observaciones: str
    reserva: str | None = None

    def aprobar(self) -> bool:
        if self.estado != EstadoDeSolicitudPrestamo.PENDIENTE:
            return False

        self.estado = EstadoDeSolicitudPrestamo.APROBADO
        return True

    def rechazar(self) -> bool:
        if self.estado != EstadoDeSolicitudPrestamo.PENDIENTE:
            return False

        self.estado = EstadoDeSolicitudPrestamo.RECHAZADO
        return True

    def cancelar(self) -> bool:
        if self.estado != EstadoDeSolicitudPrestamo.PENDIENTE:
            return False

        self.estado = EstadoDeSolicitudPrestamo.CANCELADO
        return True

    def esta_pendiente(self) -> bool:
        return self.estado == EstadoDeSolicitudPrestamo.PENDIENTE
