from dataclasses import dataclass
from datetime import date
from typing import Optional

from backend.recursos.domain.enums import EstadoFisico
from backend.shared.errors import DomainError


@dataclass
class Devolucion:
    """Registro de la devolución de un préstamo (RF13, RF10).

    Atributos del diagrama: id_devolucion, fecha_devolucion, estado_fisico, observaciones.
    Agregado: id_prestamo (la relación "Termina con" del diagrama: un préstamo, 0..1 devolución).
    """

    id_prestamo: int
    fecha_devolucion: date
    estado_fisico: EstadoFisico = EstadoFisico.BUENO
    observaciones: str = ""
    id_devolucion: Optional[int] = None

    # ---------- UML: registrar() ----------

    def registrar(self, fecha_de_retorno: date, observaciones: str,
                  estado_fisico: EstadoFisico) -> None:
        if not isinstance(estado_fisico, EstadoFisico):
            raise DomainError("El estado físico debe ser BUENO, REGULAR o DANHADO.")
        self.fecha_devolucion = fecha_de_retorno
        self.observaciones = observaciones
        self.estado_fisico = estado_fisico

    # ---------- UML: evaluarEstadoFisico() ----------

    def evaluar_estado_fisico(self) -> EstadoFisico:
        """Devuelve el estado físico con el que volvió el objeto."""
        return self.estado_fisico

    # ---------- UML: estaDanado() ----------

    def esta_danado(self) -> bool:
        return self.estado_fisico == EstadoFisico.DANHADO

    # ---------- UML: requierePenalizacion() ----------

    def requiere_penalizacion(self, fuera_de_plazo: bool = False) -> bool:
        """True si volvió dañado o tarde (fuera_de_plazo lo calcula quien conoce el Prestamo)."""
        return self.esta_danado() or fuera_de_plazo
