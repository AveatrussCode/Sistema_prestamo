from dataclasses import dataclass
from datetime import date

from backend.control.domain.enums import EstadoNotificacion


@dataclass
class Notificacion:
    id_notificacion: int
    destinatario: str
    mensaje: str
    motivo: str
    fecha: date
    estado: EstadoNotificacion

    def enviar(self):
        self.estado = EstadoNotificacion.ENVIADA

    def marcar_enviada(self):
        self.estado = EstadoNotificacion.ENVIADA

    def marcar_fallida(self):
        self.estado = EstadoNotificacion.FALLIDA