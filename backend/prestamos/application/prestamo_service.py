from datetime import date
from sqlalchemy import select, update, exists
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.prestamos.domain.Prestamo import Prestamo
from backend.prestamos.domain.devolucion import Devolucion
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.prestamos.domain.reserva import EstadoReserva
from backend.prestamos.infraestructure.models import PrestamoModel, ReservaModel, DevolucionModel
from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
from backend.recursos.infraestructure.models import ObjetoModel
from backend.shared.errors import ConflictError, DomainError, NotFoundError
from backend.usuarios.domain.usuario import EstadoUsuario
from backend.usuarios.infraestructure.models import UsuarioModel


class PrestamoService:
    def __init__(self, db: Session):
        self.db = db

    def entregar(self, reserva_id: int, administrador_id: int, observaciones: str = ''):
        reserva = self.db.get(ReservaModel, reserva_id)
        if reserva is None:
            raise NotFoundError('La reserva no existe.')
        if reserva.estado != EstadoReserva.CONFIRMADA:
            raise ConflictError('La entrega requiere una reserva confirmada que no haya sido utilizada.')
        hoy = date.today()
        if hoy < reserva.fecha_inicio:
            raise DomainError('La entrega solo puede registrarse desde la fecha de inicio de la reserva.')
        if hoy > reserva.fecha_fin:
            raise DomainError('La reserva ya venció; no se puede entregar el equipo.')
        usuario = self.db.get(UsuarioModel, reserva.usuario_id)
        if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
            raise DomainError('El usuario debe estar activo para recibir el equipo.')
        equipo = self.db.get(ObjetoModel, reserva.objeto_id)
        if equipo is None:
            raise NotFoundError('El equipo ya no existe.')
        # Las dos transiciones y el préstamo se confirman juntos; un fallo revierte todo.
        try:
            ocupado = exists(select(PrestamoModel.id).where(
                PrestamoModel.objeto_id == reserva.objeto_id, PrestamoModel.estado == EstadoPrestamo.ACTIVO))
            changed = self.db.execute(update(ObjetoModel).where(
                ObjetoModel.id == reserva.objeto_id,
                ObjetoModel.estado_disponibilidad == EstadoDeDisponibilidad.DISPONIBLE,
                ObjetoModel.estado_fisico != EstadoFisico.DANHADO, ~ocupado,
            ).values(estado_disponibilidad=EstadoDeDisponibilidad.PRESTADO), execution_options={'synchronize_session': False})
            if changed.rowcount != 1:
                raise ConflictError('El equipo no está disponible, está dañado o ya tiene un préstamo activo.')
            changed = self.db.execute(update(ReservaModel).where(
                ReservaModel.id == reserva_id, ReservaModel.estado == EstadoReserva.CONFIRMADA,
            ).values(estado=EstadoReserva.FINALIZADA), execution_options={'synchronize_session': False})
            if changed.rowcount != 1:
                raise ConflictError('La reserva ya fue procesada; actualiza el listado.')
            prestamo = PrestamoModel(reserva_id=reserva_id, usuario_id=reserva.usuario_id,
                objeto_id=reserva.objeto_id, entregado_por=administrador_id,
                usuario_nombre=usuario.nombre, objeto_nombre=equipo.nombre,
                fecha_inicio=hoy, fecha_devolucion_prevista=reserva.fecha_fin,
                estado=EstadoPrestamo.ACTIVO, observaciones_entrega=observaciones)
            self.db.add(prestamo)
            self.db.commit()
            self.db.refresh(prestamo)
            return prestamo
        except IntegrityError:
            self.db.rollback()
            raise ConflictError('La entrega ya fue registrada o el equipo tiene otro préstamo activo.')
        except Exception:
            self.db.rollback()
            raise

    def devolver(self, prestamo_id: int, administrador_id: int, estado_fisico: EstadoFisico, observaciones: str = ''):
        modelo = self.db.get(PrestamoModel, prestamo_id)
        if modelo is None:
            raise NotFoundError('El préstamo no existe.')
        if modelo.estado != EstadoPrestamo.ACTIVO:
            raise ConflictError('La devolución ya fue registrada o el préstamo no está activo.')
        hoy = date.today()
        entidad = Prestamo(modelo.id, modelo.usuario_id, modelo.objeto_id, modelo.fecha_inicio,
                           modelo.fecha_devolucion_prevista, modelo.fecha_devolucion_real, modelo.estado)
        try:
            entidad.registrar_devolucion(hoy)
        except ValueError as error:
            raise DomainError(str(error))
        devolucion = Devolucion(prestamo_id, hoy)
        devolucion.registrar(hoy, observaciones, estado_fisico)
        if devolucion.esta_danado() and not observaciones.strip():
            raise DomainError('Describe el daño del equipo en las observaciones.')
        try:
            changed = self.db.execute(update(PrestamoModel).where(
                PrestamoModel.id == prestamo_id, PrestamoModel.estado == EstadoPrestamo.ACTIVO,
            ).values(estado=entidad.estado, fecha_devolucion_real=hoy), execution_options={'synchronize_session': False})
            if changed.rowcount != 1:
                raise ConflictError('La devolución ya fue registrada; actualiza el listado.')
            disponibilidad = EstadoDeDisponibilidad.NO_DISPONIBLE if devolucion.esta_danado() else EstadoDeDisponibilidad.DISPONIBLE
            changed = self.db.execute(update(ObjetoModel).where(
                ObjetoModel.id == modelo.objeto_id,
                ObjetoModel.estado_disponibilidad == EstadoDeDisponibilidad.PRESTADO,
            ).values(estado_fisico=estado_fisico, estado_disponibilidad=disponibilidad), execution_options={'synchronize_session': False})
            if changed.rowcount != 1:
                raise ConflictError('El equipo no figura como prestado. Revisa su inventario antes de registrar la devolución.')
            self.db.add(DevolucionModel(prestamo_id=prestamo_id, fecha_devolucion=hoy,
                estado_fisico=estado_fisico, observaciones=observaciones, recibido_por=administrador_id))
            self.db.commit()
            self.db.refresh(modelo)
            return modelo
        except IntegrityError:
            self.db.rollback()
            raise ConflictError('La devolución de este préstamo ya fue registrada.')
        except Exception:
            self.db.rollback()
            raise

    def listar(self, usuario_id: int | None = None):
        query = select(PrestamoModel).order_by(PrestamoModel.id.desc())
        if usuario_id is not None:
            query = query.where(PrestamoModel.usuario_id == usuario_id)
        return self.db.scalars(query).all()


def prestamo_dict(modelo: PrestamoModel):
    entidad = Prestamo(modelo.id, modelo.usuario_id, modelo.objeto_id, modelo.fecha_inicio,
                       modelo.fecha_devolucion_prevista, modelo.fecha_devolucion_real, modelo.estado)
    return dict(id=modelo.id, reserva_id=modelo.reserva_id, usuario_id=modelo.usuario_id,
                objeto_id=modelo.objeto_id, entregado_por=modelo.entregado_por,
                usuario=modelo.usuario_nombre, equipo=modelo.objeto_nombre,
                fecha_inicio=modelo.fecha_inicio, fecha_devolucion_prevista=modelo.fecha_devolucion_prevista,
                fecha_devolucion_real=modelo.fecha_devolucion_real,
                estado='VENCIDO' if entidad.esta_vencido() else modelo.estado.name,
                observaciones_entrega=modelo.observaciones_entrega,
                devolucion=None if modelo.devolucion is None else dict(
                    fecha=modelo.devolucion.fecha_devolucion,
                    estado_fisico=modelo.devolucion.estado_fisico.value,
                    observaciones=modelo.devolucion.observaciones,
                    recibido_por=modelo.devolucion.recibido_por,
                    fuera_de_plazo=modelo.devolucion.fecha_devolucion > modelo.fecha_devolucion_prevista))
