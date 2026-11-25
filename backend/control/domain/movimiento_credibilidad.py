from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from backend.control.domain.enums import EstadoMovimiento
from backend.control.domain.politica_credibilidad import TipoMovimiento
from backend.shared.errors import DomainError

SANCIONES = {TipoMovimiento.DEVOLUCION_TARDIA, TipoMovimiento.EQUIPO_REGULAR, TipoMovimiento.EQUIPO_DANADO,
             TipoMovimiento.RESERVA_NO_RECOGIDA, TipoMovimiento.CANCELACION_TARDIA}


@dataclass
class MovimientoCredibilidad:
    """Una fila del historial: cada vez que sube o baja la credibilidad (reemplaza a Penalizacion)."""
    usuario_id: int
    tipo: TipoMovimiento
    puntos: float                  # lo que REALMENTE se sumó o restó (con signo)
    valor_antes: float
    valor_despues: float
    motivo: str
    fecha: datetime
    estado: EstadoMovimiento = EstadoMovimiento.APLICADO
    prestamo_id: Optional[int] = None
    reserva_id: Optional[int] = None
    anula_a: Optional[int] = None          # en una ANULACION: id del movimiento que se perdonó
    realizado_por: Optional[int] = None    # id del administrador; None = lo hizo el sistema
    id: Optional[int] = None

    def es_sancion(self) -> bool:
        return self.tipo in SANCIONES

    def anular(self) -> None:
        if not self.es_sancion():
            raise DomainError("Solo se puede anular una sanción.")
        if self.estado == EstadoMovimiento.ANULADO:
            raise DomainError("Esa sanción ya fue anulada.")
        self.estado = EstadoMovimiento.ANULADO
