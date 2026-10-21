from typing import Optional

from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
from backend.shared.errors import DomainError


class Objeto:
    """Objeto prestable del inventario (RF05-RF10)."""

    def __init__(self, nombre: str, descripcion: str, categoria_id: int,
                 id_objeto: Optional[int] = None,
                 estado_disponibilidad: EstadoDeDisponibilidad = EstadoDeDisponibilidad.DISPONIBLE,
                 estado_fisico: EstadoFisico = EstadoFisico.BUENO):
        self.id_objeto = id_objeto          # None hasta que se guarde en la base de datos
        self.nombre = nombre
        self.descripcion = descripcion
        self.categoria_id = categoria_id
        self.estado_disponibilidad = estado_disponibilidad
        self.estado_fisico = estado_fisico

    # ---------- consultas ----------

    def esta_disponible(self) -> bool:
        return self.estado_disponibilidad == EstadoDeDisponibilidad.DISPONIBLE

    def esta_operativo(self) -> bool:
        return self.estado_fisico != EstadoFisico.DANHADO

    def es_reservable(self) -> bool:
        """Se puede reservar (para fechas futuras) si no está dañado, no disponible ni dado de baja.

        Un objeto PRESTADO o RESERVADO hoy sí se puede reservar para otras fechas;
        el cruce de fechas lo controla ReservaService.
        """
        return self.esta_operativo() and self.estado_disponibilidad not in (
            EstadoDeDisponibilidad.NO_DISPONIBLE,
            EstadoDeDisponibilidad.DADO_DE_BAJA,
        )

    # ---------- cambios de disponibilidad ----------

    def marcar_disponible(self) -> bool:
        self._exigir_no_baja()
        self.estado_disponibilidad = EstadoDeDisponibilidad.DISPONIBLE
        return True

    def marcar_prestado(self) -> bool:
        self._exigir_no_baja()
        self.estado_disponibilidad = EstadoDeDisponibilidad.PRESTADO
        return True

    def marcar_reservado(self) -> bool:
        self._exigir_no_baja()
        self.estado_disponibilidad = EstadoDeDisponibilidad.RESERVADO
        return True

    def marcar_no_disponible(self) -> bool:
        self._exigir_no_baja()
        self.estado_disponibilidad = EstadoDeDisponibilidad.NO_DISPONIBLE
        return True

    def dar_de_baja(self) -> bool:
        if self.estado_disponibilidad == EstadoDeDisponibilidad.PRESTADO:
            raise DomainError("No se puede dar de baja un objeto que está prestado.")
        self.estado_disponibilidad = EstadoDeDisponibilidad.DADO_DE_BAJA
        return True

    # ---------- estado físico (RF10) ----------

    def actualizar_estado_fisico(self, estado: EstadoFisico) -> None:
        if not isinstance(estado, EstadoFisico):
            raise DomainError("El estado físico debe ser BUENO, REGULAR o DANHADO.")
        self.estado_fisico = estado

    def _exigir_no_baja(self) -> None:
        if self.estado_disponibilidad == EstadoDeDisponibilidad.DADO_DE_BAJA:
            raise DomainError("El objeto está dado de baja.")
