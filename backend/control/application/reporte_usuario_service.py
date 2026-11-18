"""Caso de uso: generar el REPORTE DE USUARIO (préstamos y reservas de una persona).

La aplicación decide QUÉ contiene el reporte. No sabe de SQL ni de HTTP:
pide los datos al repositorio (interfaz) y arma un Reporte.
"""
from backend.control.application.etiquetas import ESTADO_FISICO, ESTADO_RESERVA, etiqueta, fecha as _fecha
from backend.control.domain.reporte import Columna, DatoResumen, Reporte, Tabla
from backend.control.domain.usuario_reporte_repository import UsuarioReporteRepository
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.shared.errors import NotFoundError


class ReporteUsuarioService:

    def __init__(self, repo: UsuarioReporteRepository):
        self._repo = repo

    def generar(self, id_usuario: int) -> Reporte:
        usuario = self._repo.datos_de(id_usuario)
        if usuario is None:
            raise NotFoundError("Usuario no encontrado.")
        prestamos = self._repo.prestamos_de(id_usuario)
        reservas = self._repo.reservas_de(id_usuario)

        sin_devolver = [p for p in prestamos if p.prestamo.estado == EstadoPrestamo.ACTIVO]
        vencidos = [p for p in prestamos if p.prestamo.esta_vencido()]
        con_retraso = [p for p in prestamos if p.situacion() == "Devuelto con retraso"]
        danados = [p for p in prestamos if p.estado_fisico == "DANHADO"]

        filas_prestamos = [{
            "equipo": p.equipo,
            "fecha_inicio": _fecha(p.prestamo.fecha_inicio),
            "fecha_prevista": _fecha(p.prestamo.fecha_devolucion_prevista),
            "fecha_devolucion": _fecha(p.fecha_real()),
            "situacion": p.situacion(),
            "estado_fisico": etiqueta(ESTADO_FISICO, p.estado_fisico),
            "obs_entrega": p.obs_entrega,
            "obs_devolucion": p.obs_devolucion,
        } for p in prestamos]

        filas_reservas = [{
            "equipo": r.equipo,
            "desde": _fecha(r.fecha_inicio),
            "hasta": _fecha(r.fecha_fin),
            "estado": etiqueta(ESTADO_RESERVA, r.estado),
        } for r in reservas]

        return Reporte(
            titulo=f"Reporte de usuario: {usuario.nombre}",
            resumen=[
                DatoResumen("Correo", usuario.correo),
                DatoResumen("Tipo", usuario.tipo.capitalize()),
                DatoResumen("Estado de la cuenta", usuario.estado.capitalize()),
                DatoResumen("Credibilidad", usuario.credibilidad),
                DatoResumen("Préstamos realizados", len(prestamos)),
                DatoResumen("Equipos sin devolver", len(sin_devolver)),
                DatoResumen("Vencidos", len(vencidos)),
                DatoResumen("Devueltos con retraso", len(con_retraso)),
                DatoResumen("Devueltos dañados", len(danados)),
                DatoResumen("Reservas realizadas", len(reservas)),
            ],
            tablas=[
                Tabla("Préstamos", [
                    Columna("equipo", "Equipo"),
                    Columna("fecha_inicio", "Prestado el"),
                    Columna("fecha_prevista", "Debía devolver el"),
                    Columna("fecha_devolucion", "Devolvió el"),
                    Columna("situacion", "Situación"),
                    Columna("estado_fisico", "Estado al devolver"),
                    Columna("obs_entrega", "Obs. de entrega"),
                    Columna("obs_devolucion", "Obs. de devolución"),
                ], filas_prestamos),
                Tabla("Reservas", [
                    Columna("equipo", "Equipo"),
                    Columna("desde", "Desde"),
                    Columna("hasta", "Hasta"),
                    Columna("estado", "Estado"),
                ], filas_reservas),
            ],
        )
