from dataclasses import dataclass
from datetime import date

from backend.control.domain.enums import EstadoPenalizacion


@dataclass
class Penalizacion:
    id_penalizacion: int
    id_usuario: int
    motivo: str
    monto: float
    fecha: date
    estado: EstadoPenalizacion

    def aplicar(self):
        self.estado = EstadoPenalizacion.ACTIVA

    def pagar(self):
        self.estado = EstadoPenalizacion.PAGADA

    def cancelar(self):
        self.estado = EstadoPenalizacion.CANCELADA

    def esta_activa(self):
        return self.estado == EstadoPenalizacion.ACTIVA