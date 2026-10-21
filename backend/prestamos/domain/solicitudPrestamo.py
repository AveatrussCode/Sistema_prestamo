
from backend.prestamos.domain.enums import EstadoDeSolicitudPrestamo

class SolicitudPrestamo:
    id_solicitud:int
    fechaSolicitud: date
    estado: string
    observaciones : string
    reserva : string


    def aprobar(self) -> bool:
        self.estado = EstadoDeSolicitudPrestamo.APROBADO
        return True

    def rechazar(self) -> bool:
        self.estado = EstadoDeSolicitudPrestamo.RECHAZADO
        return True
    
    def cancelar(self) -> bool:
        self.estado = EstadoDeSolicitudPrestamo.CANCELADO
        return True

    def estaPendiente(self) -> bool:
        self.estado = EstadoDeSolicitudPrestamo.CANCELADO
        return True

    
    