from dataclasses import dataclass
from typing import Optional

from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
from backend.shared.errors import DomainError


@dataclass
class Objeto:
    nombre: str
    descripcion: str
    categoria_id: int
    id: Optional[int] = None
    estado_disponibilidad: EstadoDeDisponibilidad = EstadoDeDisponibilidad.DISPONIBLE
    estado_fisico: EstadoFisico = EstadoFisico.BUENO
    imagen_path: Optional[str] = None

    def __post_init__(self):
        if not self.nombre or not self.nombre.strip():
            raise DomainError("El objeto debe tener nombre.")
        if not self.categoria_id:
            raise DomainError("El objeto debe tener categoría.")

    def esta_disponible(self) -> bool:
        return self.estado_disponibilidad == EstadoDeDisponibilidad.DISPONIBLE

    def esta_operativo(self) -> bool:
        return self.estado_fisico != EstadoFisico.DANHADO

    def es_reservable(self) -> bool:
        return self.esta_disponible() and self.esta_operativo()

    def marcar_disponible(self) -> None:
        self.estado_disponibilidad = EstadoDeDisponibilidad.DISPONIBLE

    def marcar_prestado(self) -> None:
        self.estado_disponibilidad = EstadoDeDisponibilidad.PRESTADO

    def marcar_reservado(self) -> None:
        self.estado_disponibilidad = EstadoDeDisponibilidad.RESERVADO

    def marcar_no_disponible(self) -> None:
        self.estado_disponibilidad = EstadoDeDisponibilidad.NO_DISPONIBLE

    def dar_de_baja(self) -> None:
        self.estado_disponibilidad = EstadoDeDisponibilidad.DADO_DE_BAJA
