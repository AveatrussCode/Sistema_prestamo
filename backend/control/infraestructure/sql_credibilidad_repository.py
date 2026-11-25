from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from backend.control.domain.credibilidad_repository import CredibilidadRepository, DatosCredibilidad
from backend.control.domain.enums import EstadoMovimiento
from backend.control.domain.movimiento_credibilidad import MovimientoCredibilidad
from backend.control.domain.politica_credibilidad import TipoMovimiento
from backend.control.infraestructure.models import MovimientoCredibilidadModel as M
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.prestamos.domain.reserva import ESTADOS_ACTIVOS
from backend.prestamos.infraestructure.models import PrestamoModel, ReservaModel
from backend.usuarios.infraestructure.models import UsuarioModel


class SqlCredibilidadRepository(CredibilidadRepository):
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _a_dominio(m: M) -> MovimientoCredibilidad:
        return MovimientoCredibilidad(
            id=m.id, usuario_id=m.usuario_id, tipo=m.tipo, puntos=m.puntos, valor_antes=m.valor_antes,
            valor_despues=m.valor_despues, motivo=m.motivo, fecha=m.fecha, estado=m.estado,
            prestamo_id=m.prestamo_id, reserva_id=m.reserva_id, anula_a=m.anula_a, realizado_por=m.realizado_por)

    def obtener_usuario(self, usuario_id: int) -> Optional[DatosCredibilidad]:
        u = self.db.get(UsuarioModel, usuario_id)
        return None if u is None else DatosCredibilidad(u.id, u.tipo or "estudiante", float(u.credibilidad or 0))

    def guardar_valor(self, usuario_id: int, valor: float) -> None:
        self.db.get(UsuarioModel, usuario_id).credibilidad = valor
        self.db.flush()

    def guardar_movimiento(self, m: MovimientoCredibilidad) -> MovimientoCredibilidad:
        fila = M(usuario_id=m.usuario_id, tipo=m.tipo, puntos=m.puntos, valor_antes=m.valor_antes,
                 valor_despues=m.valor_despues, motivo=m.motivo, estado=m.estado, prestamo_id=m.prestamo_id,
                 reserva_id=m.reserva_id, anula_a=m.anula_a, realizado_por=m.realizado_por, fecha=m.fecha)
        self.db.add(fila)
        self.db.flush()
        return self._a_dominio(fila)

    def buscar_movimiento(self, movimiento_id: int) -> Optional[MovimientoCredibilidad]:
        fila = self.db.get(M, movimiento_id)
        return self._a_dominio(fila) if fila else None

    def marcar_anulado(self, movimiento_id: int) -> None:
        self.db.get(M, movimiento_id).estado = EstadoMovimiento.ANULADO
        self.db.flush()

    def listar_movimientos(self, usuario_id: int, limite: int = 20) -> list[MovimientoCredibilidad]:
        consulta = select(M).where(M.usuario_id == usuario_id).order_by(M.id.desc()).limit(limite)
        return [self._a_dominio(f) for f in self.db.scalars(consulta).all()]

    def bono_desde(self, usuario_id: int, desde: date) -> float:
        consulta = select(func.coalesce(func.sum(M.puntos), 0.0)).where(
            M.usuario_id == usuario_id, M.tipo == TipoMovimiento.DEVOLUCION_PUNTUAL,
            M.estado == EstadoMovimiento.APLICADO, M.fecha >= datetime.combine(desde, time.min))
        return float(self.db.scalar(consulta))

    def equipos_en_uso(self, usuario_id: int) -> int:
        reservas = self.db.scalar(select(func.count()).select_from(ReservaModel).where(
            ReservaModel.usuario_id == usuario_id, ReservaModel.estado.in_(ESTADOS_ACTIVOS)))
        prestamos = self.db.scalar(select(func.count()).select_from(PrestamoModel).where(
            PrestamoModel.usuario_id == usuario_id, PrestamoModel.estado == EstadoPrestamo.ACTIVO))
        return int(reservas or 0) + int(prestamos or 0)

    def tiene_prestamo_vencido(self, usuario_id: int, hoy: date) -> bool:
        return bool(self.db.scalar(select(exists().where(
            PrestamoModel.usuario_id == usuario_id, PrestamoModel.estado == EstadoPrestamo.ACTIVO,
            PrestamoModel.fecha_devolucion_prevista < hoy))))

    def confirmar(self) -> None:
        self.db.commit()
