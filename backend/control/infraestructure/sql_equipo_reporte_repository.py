"""Implementación SQL del puerto EquipoReporteRepository. Aquí SÍ se habla con la base (solo lectura)."""
from sqlalchemy.orm import Session

from backend.control.domain.equipo_reporte_repository import EquipoReporteRepository
from backend.control.domain.registro_prestamo import DatosEquipo, RegistroPrestamo, RegistroReserva
from backend.control.infraestructure.sql_registros import (
    a_registro_prestamo, a_registro_reserva, consulta_prestamos, consulta_reservas,
)
from backend.prestamos.infraestructure.models import PrestamoModel, ReservaModel
from backend.recursos.infraestructure.models import CategoriaModel, ObjetoModel


class SqlEquipoReporteRepository(EquipoReporteRepository):

    def __init__(self, db: Session):
        self.db = db

    def datos_de(self, id_equipo: int) -> DatosEquipo | None:
        o = self.db.get(ObjetoModel, id_equipo)
        if o is None:
            return None
        categoria = self.db.get(CategoriaModel, o.categoria_id)
        return DatosEquipo(
            id=o.id,
            nombre=o.nombre,
            descripcion=o.descripcion or "",
            categoria=categoria.nombre if categoria else "Sin categoría",
            disponibilidad=o.estado_disponibilidad.value,
            estado_fisico=o.estado_fisico.value,
        )

    def prestamos_de(self, id_equipo: int) -> list[RegistroPrestamo]:
        consulta = (
            consulta_prestamos()
            .where(PrestamoModel.objeto_id == id_equipo)
            .order_by(PrestamoModel.fecha_inicio.desc(), PrestamoModel.id.desc())
        )
        return [a_registro_prestamo(f) for f in self.db.execute(consulta).all()]

    def reservas_de(self, id_equipo: int) -> list[RegistroReserva]:
        consulta = (
            consulta_reservas()
            .where(ReservaModel.objeto_id == id_equipo)
            .order_by(ReservaModel.fecha_inicio.desc(), ReservaModel.id.desc())
        )
        return [a_registro_reserva(f) for f in self.db.execute(consulta).all()]
