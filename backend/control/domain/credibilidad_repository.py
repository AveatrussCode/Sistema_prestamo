from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional

from backend.control.domain.movimiento_credibilidad import MovimientoCredibilidad


@dataclass(frozen=True)
class DatosCredibilidad:
    id: int
    tipo: str          # 'estudiante' | 'profesor' | 'administrativo'
    valor: float


class CredibilidadRepository(ABC):
    """Lo que el servicio necesita saber de la base, sin saber que existe SQL.
    Los métodos de escritura NO hacen commit: lo hace confirmar() (así se une a la transacción de quien llama)."""

    @abstractmethod
    def obtener_usuario(self, usuario_id: int) -> Optional[DatosCredibilidad]: ...
    @abstractmethod
    def guardar_valor(self, usuario_id: int, valor: float) -> None: ...
    @abstractmethod
    def guardar_movimiento(self, m: MovimientoCredibilidad) -> MovimientoCredibilidad: ...
    @abstractmethod
    def buscar_movimiento(self, movimiento_id: int) -> Optional[MovimientoCredibilidad]: ...
    @abstractmethod
    def marcar_anulado(self, movimiento_id: int) -> None: ...
    @abstractmethod
    def listar_movimientos(self, usuario_id: int, limite: int = 20) -> list[MovimientoCredibilidad]: ...
    @abstractmethod
    def bono_desde(self, usuario_id: int, desde: date) -> float: ...
    @abstractmethod
    def equipos_en_uso(self, usuario_id: int) -> int: ...
    @abstractmethod
    def tiene_prestamo_vencido(self, usuario_id: int, hoy: date) -> bool: ...
    @abstractmethod
    def confirmar(self) -> None: ...
