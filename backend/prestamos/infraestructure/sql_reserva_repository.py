from datetime import date
from typing import Optional

from sqlalchemy import select, insert, literal, exists
from sqlalchemy.orm import Session

from backend.prestamos.domain.reserva import ESTADOS_ACTIVOS, EstadoReserva, Reserva
from backend.prestamos.domain.reserva_repository import ReservaRepository
from backend.prestamos.infraestructure.models import ReservaModel
from backend.shared.errors import NotFoundError, ConflictError


class SqlReservaRepository(ReservaRepository):

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _a_dominio(m: ReservaModel) -> Reserva:
        return Reserva(
            id_reserva=m.id, usuario_id=m.usuario_id, objeto_id=m.objeto_id,
            fecha_reserva=m.fecha_reserva, fecha_inicio=m.fecha_inicio,
            fecha_fin=m.fecha_fin, estado=m.estado,
        )

    def guardar(self, reserva: Reserva) -> Reserva:
        if reserva.id_reserva is None:
            # Una sola escritura condicional evita reservas simultáneas cruzadas en SQLite.
            overlap = exists(select(ReservaModel.id).where(
                ReservaModel.objeto_id == reserva.objeto_id,
                ReservaModel.estado.in_(ESTADOS_ACTIVOS),
                ReservaModel.fecha_inicio <= reserva.fecha_fin,
                ReservaModel.fecha_fin >= reserva.fecha_inicio,
            ))
            columns = ['usuario_id', 'objeto_id', 'fecha_reserva', 'fecha_inicio', 'fecha_fin', 'estado']
            values = select(literal(reserva.usuario_id), literal(reserva.objeto_id),
                            literal(reserva.fecha_reserva), literal(reserva.fecha_inicio),
                            literal(reserva.fecha_fin), literal(reserva.estado.value)).where(~overlap)
            result = self.db.execute(insert(ReservaModel).from_select(columns, values).returning(ReservaModel.id))
            new_id = result.scalar_one_or_none()
            if new_id is None:
                self.db.rollback()
                raise ConflictError('El equipo ya está reservado en esas fechas.')
            self.db.commit()
            return self._a_dominio(self.db.get(ReservaModel, new_id))
        else:
            modelo = self.db.get(ReservaModel, reserva.id_reserva)
            if modelo is None:
                raise NotFoundError(f"Reserva {reserva.id_reserva} no existe.")
        modelo.usuario_id = reserva.usuario_id
        modelo.objeto_id = reserva.objeto_id
        modelo.fecha_reserva = reserva.fecha_reserva
        modelo.fecha_inicio = reserva.fecha_inicio
        modelo.fecha_fin = reserva.fecha_fin
        modelo.estado = reserva.estado
        self.db.commit()
        self.db.refresh(modelo)
        return self._a_dominio(modelo)

    def buscar_por_id(self, id_reserva: int) -> Optional[Reserva]:
        modelo = self.db.get(ReservaModel, id_reserva)
        return self._a_dominio(modelo) if modelo else None

    def listar(self, usuario_id: Optional[int] = None, objeto_id: Optional[int] = None,
               estado: Optional[EstadoReserva] = None) -> list[Reserva]:
        consulta = select(ReservaModel).order_by(ReservaModel.fecha_inicio, ReservaModel.id)
        if usuario_id is not None:
            consulta = consulta.where(ReservaModel.usuario_id == usuario_id)
        if objeto_id is not None:
            consulta = consulta.where(ReservaModel.objeto_id == objeto_id)
        if estado is not None:
            consulta = consulta.where(ReservaModel.estado == estado)
        return [self._a_dominio(m) for m in self.db.execute(consulta).scalars().all()]

    def existe_solapada(self, objeto_id: int, fecha_inicio: date, fecha_fin: date,
                        excluir_id: Optional[int] = None) -> bool:
        # Dos rangos [a,b] y [c,d] se cruzan  <=>  a <= d  y  c <= b   (extremos incluidos)
        consulta = select(ReservaModel.id).where(
            ReservaModel.objeto_id == objeto_id,
            ReservaModel.estado.in_(ESTADOS_ACTIVOS),
            ReservaModel.fecha_inicio <= fecha_fin,
            ReservaModel.fecha_fin >= fecha_inicio,
        )
        if excluir_id is not None:
            consulta = consulta.where(ReservaModel.id != excluir_id)
        return self.db.execute(consulta.limit(1)).first() is not None
