"""Consultas y conversiones SQL que comparten el reporte de equipo y el reporte por periodo (solo lectura).

Cada repositorio parte de `consulta_prestamos()` / `consulta_reservas()` y solo le agrega su filtro y su orden.
"""
from sqlalchemy import select

from backend.control.domain.registro_prestamo import RegistroPrestamo, RegistroReserva
from backend.prestamos.domain.Prestamo import Prestamo
from backend.prestamos.infraestructure.models import DevolucionModel, PrestamoModel, ReservaModel
from backend.recursos.infraestructure.models import ObjetoModel
from backend.usuarios.infraestructure.models import UsuarioModel


def consulta_prestamos():
    # outerjoin con usuarios: si el usuario fue eliminado, el préstamo igual aparece (correo = None).
    # outerjoin con devoluciones: un préstamo sin devolver igual aparece (datos de la devolución en None).
    return (
        select(
            PrestamoModel.id,
            PrestamoModel.usuario_id,
            PrestamoModel.objeto_id,
            PrestamoModel.usuario_nombre,
            PrestamoModel.objeto_nombre,
            PrestamoModel.fecha_inicio,
            PrestamoModel.fecha_devolucion_prevista,
            PrestamoModel.fecha_devolucion_real,
            PrestamoModel.estado,
            PrestamoModel.observaciones_entrega,
            UsuarioModel.correo_institucional,
            DevolucionModel.fecha_devolucion,
            DevolucionModel.estado_fisico,
            DevolucionModel.observaciones,
        )
        .select_from(PrestamoModel)
        .outerjoin(UsuarioModel, UsuarioModel.id == PrestamoModel.usuario_id)
        .outerjoin(DevolucionModel, DevolucionModel.prestamo_id == PrestamoModel.id)
    )


def a_registro_prestamo(f) -> RegistroPrestamo:
    return RegistroPrestamo(
        prestamo=Prestamo(
            id_prestamo=f.id,
            id_usuario=f.usuario_id,
            id_objeto=f.objeto_id,
            fecha_inicio=f.fecha_inicio,
            fecha_devolucion_prevista=f.fecha_devolucion_prevista,
            fecha_devolucion_real=f.fecha_devolucion_real or f.fecha_devolucion,
            estado=f.estado,
        ),
        usuario=f.usuario_nombre,
        correo=f.correo_institucional,
        equipo=f.objeto_nombre,
        estado_fisico=f.estado_fisico.value if f.estado_fisico else None,
        obs_entrega=f.observaciones_entrega or "",
        obs_devolucion=f.observaciones or "",
    )


def consulta_reservas():
    # outerjoin: si el usuario o el equipo fueron eliminados, la reserva igual aparece.
    return (
        select(
            ReservaModel.id,
            ReservaModel.fecha_reserva,
            ReservaModel.fecha_inicio,
            ReservaModel.fecha_fin,
            ReservaModel.estado,
            UsuarioModel.nombre.label("usuario_nombre"),
            ObjetoModel.nombre.label("objeto_nombre"),
        )
        .select_from(ReservaModel)
        .outerjoin(UsuarioModel, UsuarioModel.id == ReservaModel.usuario_id)
        .outerjoin(ObjetoModel, ObjetoModel.id == ReservaModel.objeto_id)
    )


def a_registro_reserva(f) -> RegistroReserva:
    return RegistroReserva(
        id=f.id,
        usuario=f.usuario_nombre or "(usuario eliminado)",
        equipo=f.objeto_nombre or "(equipo eliminado)",
        fecha_reserva=f.fecha_reserva,
        fecha_inicio=f.fecha_inicio,
        fecha_fin=f.fecha_fin,
        estado=f.estado.value,
    )
