"""Implementación SQL del puerto PeriodoReporteRepository. Aquí SÍ se habla con la base (solo lectura)."""
from datetime import date

from sqlalchemy.orm import Session

from backend.control.domain.periodo_reporte_repository import PeriodoReporteRepository
from backend.control.domain.registro_prestamo import RegistroPrestamo, RegistroReserva
from backend.control.infraestructure.sql_registros import (
    a_registro_prestamo, a_registro_reserva, consulta_prestamos, consulta_reservas,
)
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.prestamos.infraestructure.models import PrestamoModel, ReservaModel


class SqlPeriodoReporteRepository(PeriodoReporteRepository):

    def __init__(self, db: Session):
        self.db = db

    def prestamos_entregados(self, desde: date, hasta: date) -> list[RegistroPrestamo]:
        consulta = (
            consulta_prestamos()
            .where(PrestamoModel.fecha_inicio >= desde, PrestamoModel.fecha_inicio <= hasta)
            .order_by(PrestamoModel.fecha_inicio, PrestamoModel.id)
        )
        return [a_registro_prestamo(f) for f in self.db.execute(consulta).all()]

    def devoluciones(self, desde: date, hasta: date) -> list[RegistroPrestamo]:
        consulta = (
            consulta_prestamos()
            .where(
                PrestamoModel.estado == EstadoPrestamo.DEVUELTO,
                PrestamoModel.fecha_devolucion_real >= desde,
                PrestamoModel.fecha_devolucion_real <= hasta,
            )
            .order_by(PrestamoModel.fecha_devolucion_real, PrestamoModel.id)
        )
        return [a_registro_prestamo(f) for f in self.db.execute(consulta).all()]

    def reservas(self, desde: date, hasta: date) -> list[RegistroReserva]:
        consulta = (
            consulta_reservas()
            .where(ReservaModel.fecha_reserva >= desde, ReservaModel.fecha_reserva <= hasta)
            .order_by(ReservaModel.fecha_reserva, ReservaModel.id)
        )
        return [a_registro_reserva(f) for f in self.db.execute(consulta).all()]
