"""Implementación SQL del puerto PendienteDevolucionRepository. Aquí SÍ se habla con la base de datos (solo lectura)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.control.domain.pendiente_devolucion import PendienteDevolucion
from backend.control.domain.pendiente_devolucion_repository import PendienteDevolucionRepository
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.prestamos.domain.Prestamo import Prestamo
from backend.prestamos.infraestructure.models import PrestamoModel
from backend.usuarios.infraestructure.models import UsuarioModel


class SqlPendienteDevolucionRepository(PendienteDevolucionRepository):

    def __init__(self, db: Session):
        self.db = db

    def listar_activos(self) -> list[PendienteDevolucion]:
        # Se piden solo las columnas necesarias (no entidades completas).
        # El préstamo guarda el nombre del usuario pero no su correo, por eso se une con `usuarios`.
        # outerjoin: si el usuario fue eliminado, el préstamo igual aparece (correo = None).
        consulta = (
            select(
                PrestamoModel.id,
                PrestamoModel.usuario_id,
                PrestamoModel.objeto_id,
                PrestamoModel.usuario_nombre,
                PrestamoModel.objeto_nombre,
                PrestamoModel.fecha_inicio,
                PrestamoModel.fecha_devolucion_prevista,
                UsuarioModel.correo_institucional,
            )
            .outerjoin(UsuarioModel, UsuarioModel.id == PrestamoModel.usuario_id)
            .where(PrestamoModel.estado == EstadoPrestamo.ACTIVO)
            .order_by(PrestamoModel.fecha_devolucion_prevista, PrestamoModel.id)
        )
        return [self._a_dominio(fila) for fila in self.db.execute(consulta).all()]

    @staticmethod
    def _a_dominio(fila) -> PendienteDevolucion:
        return PendienteDevolucion(
            prestamo=Prestamo(
                id_prestamo=fila.id,
                id_usuario=fila.usuario_id,
                id_objeto=fila.objeto_id,
                fecha_inicio=fila.fecha_inicio,
                fecha_devolucion_prevista=fila.fecha_devolucion_prevista,
                estado=EstadoPrestamo.ACTIVO,
            ),
            usuario=fila.usuario_nombre,
            correo=fila.correo_institucional,
            equipo=fila.objeto_nombre,
        )
