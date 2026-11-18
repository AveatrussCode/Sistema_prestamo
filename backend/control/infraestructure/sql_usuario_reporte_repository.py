"""Implementación SQL del puerto UsuarioReporteRepository. Aquí SÍ se habla con la base (solo lectura)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.control.domain.historial_usuario import DatosUsuario, PrestamoDeUsuario, ReservaDeUsuario
from backend.control.domain.usuario_reporte_repository import UsuarioReporteRepository
from backend.prestamos.domain.Prestamo import Prestamo
from backend.prestamos.infraestructure.models import DevolucionModel, PrestamoModel, ReservaModel
from backend.recursos.infraestructure.models import ObjetoModel
from backend.usuarios.infraestructure.models import UsuarioModel


class SqlUsuarioReporteRepository(UsuarioReporteRepository):

    def __init__(self, db: Session):
        self.db = db

    def datos_de(self, id_usuario: int) -> DatosUsuario | None:
        u = self.db.get(UsuarioModel, id_usuario)
        if u is None:
            return None
        return DatosUsuario(
            id=u.id, nombre=u.nombre, correo=u.correo_institucional, tipo=u.tipo or "",
            estado=u.estado.value if u.estado else "", credibilidad=u.credibilidad,
        )

    def prestamos_de(self, id_usuario: int) -> list[PrestamoDeUsuario]:
        # outerjoin: un préstamo sin devolver igual aparece (los datos de la devolución quedan en None).
        consulta = (
            select(
                PrestamoModel.id,
                PrestamoModel.usuario_id,
                PrestamoModel.objeto_id,
                PrestamoModel.objeto_nombre,
                PrestamoModel.fecha_inicio,
                PrestamoModel.fecha_devolucion_prevista,
                PrestamoModel.fecha_devolucion_real,
                PrestamoModel.estado,
                PrestamoModel.observaciones_entrega,
                DevolucionModel.fecha_devolucion,
                DevolucionModel.estado_fisico,
                DevolucionModel.observaciones,
            )
            .outerjoin(DevolucionModel, DevolucionModel.prestamo_id == PrestamoModel.id)
            .where(PrestamoModel.usuario_id == id_usuario)
            .order_by(PrestamoModel.fecha_inicio.desc(), PrestamoModel.id.desc())
        )
        return [self._prestamo_a_dominio(f) for f in self.db.execute(consulta).all()]

    def reservas_de(self, id_usuario: int) -> list[ReservaDeUsuario]:
        consulta = (
            select(
                ReservaModel.id,
                ReservaModel.fecha_inicio,
                ReservaModel.fecha_fin,
                ReservaModel.estado,
                ObjetoModel.nombre,
            )
            .outerjoin(ObjetoModel, ObjetoModel.id == ReservaModel.objeto_id)
            .where(ReservaModel.usuario_id == id_usuario)
            .order_by(ReservaModel.fecha_inicio.desc(), ReservaModel.id.desc())
        )
        return [
            ReservaDeUsuario(
                id=f.id, equipo=f.nombre or "(equipo eliminado)",
                fecha_inicio=f.fecha_inicio, fecha_fin=f.fecha_fin, estado=f.estado.value,
            )
            for f in self.db.execute(consulta).all()
        ]

    @staticmethod
    def _prestamo_a_dominio(f) -> PrestamoDeUsuario:
        return PrestamoDeUsuario(
            prestamo=Prestamo(
                id_prestamo=f.id,
                id_usuario=f.usuario_id,
                id_objeto=f.objeto_id,
                fecha_inicio=f.fecha_inicio,
                fecha_devolucion_prevista=f.fecha_devolucion_prevista,
                fecha_devolucion_real=f.fecha_devolucion_real or f.fecha_devolucion,
                estado=f.estado,
            ),
            equipo=f.objeto_nombre,
            estado_fisico=f.estado_fisico.value if f.estado_fisico else None,
            obs_entrega=f.observaciones_entrega or "",
            obs_devolucion=f.observaciones or "",
        )
