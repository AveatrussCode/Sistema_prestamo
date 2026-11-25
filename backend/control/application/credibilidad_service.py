from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from backend.control.domain import politica_credibilidad as P
from backend.control.domain.credibilidad_repository import CredibilidadRepository
from backend.control.domain.enums import EstadoMovimiento
from backend.control.domain.movimiento_credibilidad import MovimientoCredibilidad
from backend.control.domain.politica_credibilidad import TipoMovimiento as T
from backend.prestamos.application.ports import CredibilidadPort
from backend.recursos.domain.enums import EstadoFisico
from backend.shared.errors import DomainError, NotFoundError


@dataclass
class ResumenCredibilidad:
    valor: float
    tope: float
    porcentaje: float
    nivel: P.Nivel
    limites: P.Limites
    movimientos: list[MovimientoCredibilidad]


def _ahora() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class CredibilidadService(CredibilidadPort):
    def __init__(self, repo: CredibilidadRepository):
        self._repo = repo

    # ---------- el único punto donde cambia la credibilidad ----------

    def _aplicar(self, usuario_id: int, tipo: T, puntos: float, motivo: str, *, automatico: bool = True,
                 realizado_por: Optional[int] = None, prestamo_id: Optional[int] = None,
                 reserva_id: Optional[int] = None, anula_a: Optional[int] = None) -> Optional[MovimientoCredibilidad]:
        u = self._repo.obtener_usuario(usuario_id)
        if u is None:                       # usuario eliminado: no hay a quién sancionar
            return None
        if automatico:
            puntos = P.limitar_subida(u.valor, puntos, u.tipo)
            if puntos == 0 and tipo == T.DEVOLUCION_PUNTUAL:
                return None                 # bono que no suma nada: no se registra
        nuevo = P.acotar(u.valor + puntos, u.tipo)
        movimiento = MovimientoCredibilidad(
            usuario_id=usuario_id, tipo=tipo, puntos=nuevo - u.valor, valor_antes=u.valor, valor_despues=nuevo,
            motivo=motivo, fecha=_ahora(), prestamo_id=prestamo_id, reserva_id=reserva_id,
            anula_a=anula_a, realizado_por=realizado_por)
        self._repo.guardar_valor(usuario_id, nuevo)
        return self._repo.guardar_movimiento(movimiento)

    # ---------- eventos automáticos ----------

    def registrar_devolucion(self, usuario_id: int, prestamo_id: int, fecha_inicio: date, fecha_prevista: date,
                             fecha_real: date, estado_fisico: EstadoFisico, confirmar: bool = True) -> None:
        u = self._repo.obtener_usuario(usuario_id)
        if u is None:
            return
        dias_tarde = max(0, (fecha_real - fecha_prevista).days)
        eventos = []
        if dias_tarde:
            eventos.append((T.DEVOLUCION_TARDIA, P.puntos_devolucion_tardia(dias_tarde, u.tipo),
                            f"Devolvió {dias_tarde} día(s) tarde."))
        if estado_fisico == EstadoFisico.DANHADO:
            eventos.append((T.EQUIPO_DANADO, P.puntos(T.EQUIPO_DANADO, u.tipo), "Devolvió el equipo dañado."))
        elif estado_fisico == EstadoFisico.REGULAR:
            eventos.append((T.EQUIPO_REGULAR, P.puntos(T.EQUIPO_REGULAR, u.tipo), "Devolvió el equipo en estado regular."))
        limpia = dias_tarde == 0 and estado_fisico == EstadoFisico.BUENO and (fecha_real - fecha_inicio).days >= 1
        if limpia:                          # anti-granjeo: préstamo de 1 día o más y tope por semana
            usado = self._repo.bono_desde(usuario_id, fecha_real - timedelta(days=6))
            disponible = P.MAX_BONO_SEMANAL * P.escala(u.tipo).factor - usado
            bono = min(P.puntos(T.DEVOLUCION_PUNTUAL, u.tipo), disponible)
            if bono > 0:
                eventos.append((T.DEVOLUCION_PUNTUAL, bono, "Devolución puntual y en buen estado."))
        for tipo, pts, motivo in eventos:
            self._aplicar(usuario_id, tipo, pts, motivo, prestamo_id=prestamo_id)
        if confirmar:
            self._repo.confirmar()

    def sancionar_no_recogida(self, usuario_id: int, reserva_id: int, confirmar: bool = True) -> None:
        u = self._repo.obtener_usuario(usuario_id)
        if u is not None:
            self._aplicar(usuario_id, T.RESERVA_NO_RECOGIDA, P.puntos(T.RESERVA_NO_RECOGIDA, u.tipo),
                          "No recogió el equipo de una reserva confirmada.", reserva_id=reserva_id)
        if confirmar:
            self._repo.confirmar()

    def sancionar_cancelacion_tardia(self, usuario_id: int, reserva_id: int, confirmar: bool = True) -> None:
        u = self._repo.obtener_usuario(usuario_id)
        if u is not None:
            self._aplicar(usuario_id, T.CANCELACION_TARDIA, P.puntos(T.CANCELACION_TARDIA, u.tipo),
                          "Canceló una reserva confirmada el día de inicio o después.", reserva_id=reserva_id)
        if confirmar:
            self._repo.confirmar()

    # ---------- validaciones (la credibilidad restringe lo que se puede hacer) ----------

    def validar_reserva(self, usuario_id: int, fecha_inicio: date, fecha_fin: date, hoy: date) -> None:
        u = self._repo.obtener_usuario(usuario_id)
        if u is None:
            return
        nivel, lim = P.nivel(u.valor, u.tipo), P.limites(u.valor, u.tipo)
        etiqueta = P.ETIQUETA[nivel]
        if self._repo.tiene_prestamo_vencido(usuario_id, hoy):
            raise DomainError("Tienes un préstamo vencido. Devuélvelo antes de reservar otro equipo.")
        if not lim.puede_reservar:
            raise DomainError(f"Con tu nivel ({etiqueta}) no puedes reservar equipos. Habla con un administrador.")
        dias = (fecha_fin - fecha_inicio).days + 1
        if dias > lim.max_dias:
            raise DomainError(f"Con tu nivel ({etiqueta}) el máximo es {lim.max_dias} día(s) por reserva.")
        anticipacion = (fecha_inicio - hoy).days
        if anticipacion > lim.anticipacion_dias:
            cuando = "solo puedes reservar para hoy" if lim.anticipacion_dias == 0 \
                else f"solo puedes reservar con hasta {lim.anticipacion_dias} día(s) de anticipación"
            raise DomainError(f"Con tu nivel ({etiqueta}) {cuando}.")
        en_uso = self._repo.equipos_en_uso(usuario_id)
        if en_uso >= lim.max_equipos:
            raise DomainError(f"Con tu nivel ({etiqueta}) puedes tener {lim.max_equipos} equipo(s) a la vez "
                              f"(reservas activas + préstamos) y ya tienes {en_uso}.")

    def validar_entrega(self, usuario_id: int, hoy: date) -> None:
        if self._repo.tiene_prestamo_vencido(usuario_id, hoy):
            raise DomainError("El usuario tiene un préstamo vencido; no puede recibir otro equipo.")

    # ---------- acciones del administrador ----------

    def ajustar(self, usuario_id: int, admin_id: int, motivo: str, *, valor: Optional[float] = None,
                delta: Optional[float] = None) -> MovimientoCredibilidad:
        if not motivo or not motivo.strip():
            raise DomainError("El motivo del ajuste es obligatorio.")
        u = self._repo.obtener_usuario(usuario_id)
        if u is None:
            raise NotFoundError(f"Usuario {usuario_id} no existe.")
        tope = P.escala(u.tipo).tope
        if valor is not None:
            if not 0 <= valor <= tope:
                raise DomainError(f"La credibilidad de un {u.tipo} debe estar entre 0 y {tope:g}.")
            puntos = valor - u.valor
        elif delta is not None:
            puntos = delta
        else:
            raise DomainError("Indica el valor nuevo o el cambio.")
        m = self._aplicar(usuario_id, T.AJUSTE_ADMIN, puntos, motivo.strip(), automatico=False, realizado_por=admin_id)
        self._repo.confirmar()
        return m

    def anular(self, movimiento_id: int, admin_id: int, motivo: str) -> MovimientoCredibilidad:
        if not motivo or not motivo.strip():
            raise DomainError("El motivo de la anulación es obligatorio.")
        original = self._repo.buscar_movimiento(movimiento_id)
        if original is None:
            raise NotFoundError(f"Movimiento {movimiento_id} no existe.")
        original.anular()                                   # valida: solo sanciones, una sola vez
        self._repo.marcar_anulado(movimiento_id)
        m = self._aplicar(original.usuario_id, T.ANULACION, -original.puntos, f"Anulación: {motivo.strip()}",
                          automatico=False, realizado_por=admin_id, anula_a=movimiento_id)
        self._repo.confirmar()
        return m

    # ---------- consulta ----------

    def resumen(self, usuario_id: int, limite: int = 20) -> ResumenCredibilidad:
        u = self._repo.obtener_usuario(usuario_id)
        if u is None:
            raise NotFoundError(f"Usuario {usuario_id} no existe.")
        return ResumenCredibilidad(u.valor, P.escala(u.tipo).tope, round(P.porcentaje(u.valor, u.tipo), 1),
                                   P.nivel(u.valor, u.tipo), P.limites(u.valor, u.tipo),
                                   self._repo.listar_movimientos(usuario_id, limite))
