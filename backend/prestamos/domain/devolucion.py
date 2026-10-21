
from dataclasses import dataclass
from datetime import date
from backend.prestamos.domain.enums import EstadoFisico


@dataclass
class Devolucion:
    id_devolucion: int
    fecha_devolucion: date
    estado_fisico: EstadoFisico
    observaciones: str

    def registrar(
        self,
        fecha_de_retorno: date,
        observaciones: str,
        estado_fisico: EstadoFisico,
    ) -> None:
        self.fecha_devolucion = fecha_de_retorno
        self.observaciones = observaciones
        self.estado_fisico = estado_fisico

    def evaluar_estado_fisico(
        self,
        estado_fisico: EstadoFisico,
    ) -> None:
        self.estado_fisico = estado_fisico

    def esta_danado(self) -> bool:
        return self.estado_fisico == EstadoFisico.DANADO

    def requiere_penalizacion(self) -> bool:
        return self.esta_danado()
