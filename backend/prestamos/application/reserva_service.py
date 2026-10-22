from datetime import date
from typing import Optional

from backend.prestamos.application.ports import UsuarioLookup
from backend.prestamos.domain.reserva import EstadoReserva, Reserva
from backend.prestamos.domain.reserva_repository import ReservaRepository
from backend.recursos.domain.objeto_repository import ObjetoRepository
from backend.shared.errors import ConflictError, DomainError, NotFoundError
from backend.usuarios.domain.usuario import EstadoUsuario


class ReservaService:
    """Casos de uso de Reserva (RF17, RF18). Aquí viven las REGLAS que involucran varias cosas."""

    def __init__(self, reservas: ReservaRepository, objetos: ObjetoRepository,
                 usuarios: UsuarioLookup):
        self._reservas = reservas
        self._objetos = objetos
        self._usuarios = usuarios

    # ---------- crear ----------

    def crear(self, usuario_id: int, objeto_id: int, fecha_inicio: date, fecha_fin: date,
              hoy: Optional[date] = None) -> Reserva:
        hoy = hoy or date.today()          # 'hoy' se puede inyectar -> pruebas predecibles

        # 1) Reglas propias de la reserva (fechas coherentes)
        reserva = Reserva(usuario_id=usuario_id, objeto_id=objeto_id,
                          fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, fecha_reserva=hoy)
        if fecha_inicio < hoy:
            raise DomainError("No se puede reservar en una fecha pasada.")

        # 2) El usuario debe existir y estar activo
        usuario = self._usuarios.obtener_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError(f"Usuario {usuario_id} no existe.")
        if usuario.estado != EstadoUsuario.ACTIVO:
            raise DomainError("El usuario no está activo; no puede reservar.")

        # 3) El objeto debe existir y poder reservarse
        objeto = self._objetos.buscar_por_id(objeto_id)
        if objeto is None:
            raise NotFoundError(f"Objeto {objeto_id} no existe.")
        if not objeto.es_reservable():
            raise DomainError("El objeto no se puede reservar (dañado, no disponible o dado de baja).")

        # 4) Las fechas no pueden cruzarse con otra reserva activa del mismo objeto
        if self._reservas.existe_solapada(objeto_id, fecha_inicio, fecha_fin):
            raise ConflictError("El objeto ya está reservado en esas fechas.")

        return self._reservas.guardar(reserva)

    # ---------- consultar (RF18) ----------

    def obtener(self, id_reserva: int) -> Reserva:
        reserva = self._reservas.buscar_por_id(id_reserva)
        if reserva is None:
            raise NotFoundError(f"Reserva {id_reserva} no existe.")
        return reserva

    def listar(self, usuario_id: Optional[int] = None, objeto_id: Optional[int] = None,
               estado: Optional[EstadoReserva] = None) -> list[Reserva]:
        return self._reservas.listar(usuario_id, objeto_id, estado)

    # ---------- cambios de estado ----------
    # Patrón: obtener -> la entidad aplica la regla -> guardar

    def confirmar(self, id_reserva: int) -> Reserva:
        reserva = self.obtener(id_reserva)
        if reserva.esta_vencida():
            raise DomainError('La reserva ya venció; no se puede confirmar.')
        usuario = self._usuarios.obtener_por_id(reserva.usuario_id)
        if usuario is None or usuario.estado != EstadoUsuario.ACTIVO:
            raise DomainError('El usuario ya no está activo; no se puede confirmar la reserva.')
        objeto = self._objetos.buscar_por_id(reserva.objeto_id)
        if objeto is None or not objeto.es_reservable():
            raise DomainError('El equipo ya no está disponible o está dañado; no se puede confirmar.')
        reserva.confirmar()
        return self._reservas.guardar(reserva)

    def cancelar(self, id_reserva: int) -> Reserva:
        reserva = self.obtener(id_reserva)
        reserva.cancelar()
        return self._reservas.guardar(reserva)

    def finalizar(self, id_reserva: int) -> Reserva:
        reserva = self.obtener(id_reserva)
        reserva.finalizar()
        return self._reservas.guardar(reserva)

    def marcar_vencidas(self, hoy: Optional[date] = None) -> list[Reserva]:
        """Pasa a VENCIDA toda reserva activa cuya fecha_fin ya pasó. Devuelve las que cambió."""
        hoy = hoy or date.today()
        vencidas = []
        for estado in (EstadoReserva.PENDIENTE, EstadoReserva.CONFIRMADA):
            for reserva in self._reservas.listar(estado=estado):
                if reserva.esta_vencida(hoy):
                    reserva.marcar_vencida()
                    vencidas.append(self._reservas.guardar(reserva))
        return vencidas
