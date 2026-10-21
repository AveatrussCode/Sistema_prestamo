from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional

from backend.shared.errors import DomainError


class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"      # recién creada
    CONFIRMADA = "CONFIRMADA"    # aprobada por un administrativo
    FINALIZADA = "FINALIZADA"    # ya se usó (se convirtió en préstamo / terminó)
    CANCELADA = "CANCELADA"
    VENCIDA = "VENCIDA"          # pasó su fecha_fin sin finalizarse


# Estados en los que la reserva "ocupa" el objeto en esas fechas.
ESTADOS_ACTIVOS = (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA)


@dataclass
class Reserva:
    usuario_id: int
    objeto_id: int
    fecha_inicio: date
    fecha_fin: date
    id_reserva: Optional[int] = None
    fecha_reserva: date = field(default_factory=date.today)   # cuándo se hizo la reserva
    estado: EstadoReserva = EstadoReserva.PENDIENTE

    def __post_init__(self):
        if self.fecha_fin < self.fecha_inicio:
            raise DomainError("La fecha de fin no puede ser anterior a la de inicio.")

    # ---------- consultas (UML: estaActiva, estaVencida) ----------

    def esta_activa(self) -> bool:
        return self.estado in ESTADOS_ACTIVOS

    def esta_vencida(self, hoy: Optional[date] = None) -> bool:
        hoy = hoy or date.today()
        return self.esta_activa() and hoy > self.fecha_fin

    # ---------- transiciones (UML: confirmar, cancelar, finalizar) ----------

    def confirmar(self) -> None:
        if self.estado != EstadoReserva.PENDIENTE:
            raise DomainError(f"Solo se puede confirmar una reserva PENDIENTE (está {self.estado.value}).")
        self.estado = EstadoReserva.CONFIRMADA

    def cancelar(self) -> None:
        if not self.esta_activa():
            raise DomainError(f"No se puede cancelar una reserva {self.estado.value}.")
        self.estado = EstadoReserva.CANCELADA

    def finalizar(self) -> None:
        if self.estado != EstadoReserva.CONFIRMADA:
            raise DomainError(f"Solo se puede finalizar una reserva CONFIRMADA (está {self.estado.value}).")
        self.estado = EstadoReserva.FINALIZADA

    def marcar_vencida(self) -> None:
        if not self.esta_activa():
            raise DomainError(f"Una reserva {self.estado.value} no puede pasar a VENCIDA.")
        self.estado = EstadoReserva.VENCIDA
