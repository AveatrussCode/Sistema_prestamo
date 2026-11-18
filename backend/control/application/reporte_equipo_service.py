"""Caso de uso: generar el REPORTE DE EQUIPO (por qué manos pasó, en qué estado quedó y qué se observó).

La aplicación decide QUÉ contiene el reporte. No sabe de SQL ni de HTTP:
pide los datos al repositorio (interfaz) y arma un Reporte.
"""
from backend.control.application.etiquetas import DISPONIBILIDAD, ESTADO_FISICO, ESTADO_RESERVA, etiqueta, fecha
from backend.control.domain.equipo_reporte_repository import EquipoReporteRepository
from backend.control.domain.reporte import Columna, DatoResumen, Reporte, Tabla
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.shared.errors import NotFoundError


class ReporteEquipoService:

    def __init__(self, repo: EquipoReporteRepository):
        self._repo = repo

    def generar(self, id_equipo: int) -> Reporte:
        equipo = self._repo.datos_de(id_equipo)
        if equipo is None:
            raise NotFoundError("Equipo no encontrado.")
        prestamos = self._repo.prestamos_de(id_equipo)
        reservas = self._repo.reservas_de(id_equipo)

        # Un préstamo cancelado nunca llegó a usarse: no cuenta como "vez prestado".
        usados = [p for p in prestamos if p.prestamo.estado != EstadoPrestamo.CANCELADO]
        sin_devolver = [p for p in prestamos if p.prestamo.estado == EstadoPrestamo.ACTIVO]
        con_retraso = [p for p in prestamos if p.devuelto_con_retraso()]
        danados = [p for p in prestamos if p.estado_fisico == "DANHADO"]
        personas = {p.prestamo.id_usuario for p in usados}
        dias_total = sum(p.dias_en_poder() or 0 for p in usados)

        filas_prestamos = [{
            "usuario": p.usuario,
            "correo": p.correo,
            "fecha_inicio": fecha(p.prestamo.fecha_inicio),
            "fecha_prevista": fecha(p.prestamo.fecha_devolucion_prevista),
            "fecha_devolucion": fecha(p.fecha_real()),
            "dias": p.dias_en_poder(),
            "situacion": p.situacion(),
            "estado_fisico": etiqueta(ESTADO_FISICO, p.estado_fisico),
            "obs_entrega": p.obs_entrega,
            "obs_devolucion": p.obs_devolucion,
        } for p in prestamos]

        # Línea de tiempo del estado del equipo: cada devolución dice cómo quedó,
        # y cada entrega/devolución con comentarios deja su observación.
        eventos = []
        for p in prestamos:
            if p.obs_entrega.strip():
                eventos.append((p.prestamo.fecha_inicio, p.prestamo.id_prestamo, 0, {
                    "fecha": fecha(p.prestamo.fecha_inicio),
                    "momento": "Entrega",
                    "usuario": p.usuario,
                    "estado_fisico": "",
                    "observacion": p.obs_entrega,
                }))
            if p.estado_fisico is not None:
                dia = p.fecha_real() or p.prestamo.fecha_inicio
                eventos.append((dia, p.prestamo.id_prestamo, 1, {
                    "fecha": fecha(dia),
                    "momento": "Devolución",
                    "usuario": p.usuario,
                    "estado_fisico": etiqueta(ESTADO_FISICO, p.estado_fisico),
                    "observacion": p.obs_devolucion,
                }))
        eventos.sort(key=lambda e: e[:3], reverse=True)  # lo más reciente primero
        filas_observaciones = [e[3] for e in eventos]

        filas_reservas = [{
            "usuario": r.usuario,
            "fecha_reserva": fecha(r.fecha_reserva),
            "desde": fecha(r.fecha_inicio),
            "hasta": fecha(r.fecha_fin),
            "estado": etiqueta(ESTADO_RESERVA, r.estado),
        } for r in reservas]

        return Reporte(
            titulo=f"Reporte de equipo: {equipo.nombre}",
            resumen=[
                DatoResumen("Categoría", equipo.categoria),
                DatoResumen("Disponibilidad actual", etiqueta(DISPONIBILIDAD, equipo.disponibilidad)),
                DatoResumen("Estado físico actual", etiqueta(ESTADO_FISICO, equipo.estado_fisico)),
                DatoResumen("Veces prestado", len(usados)),
                DatoResumen("Sin devolver", len(sin_devolver)),
                DatoResumen("Personas distintas", len(personas)),
                DatoResumen("Días en préstamo", dias_total),
                DatoResumen("Devuelto con retraso", len(con_retraso)),
                DatoResumen("Devuelto dañado", len(danados)),
                DatoResumen("Reservas realizadas", len(reservas)),
            ],
            tablas=[
                Tabla("Historial de préstamos", [
                    Columna("usuario", "Persona"),
                    Columna("correo", "Correo"),
                    Columna("fecha_inicio", "Prestado el"),
                    Columna("fecha_prevista", "Debía devolver el"),
                    Columna("fecha_devolucion", "Devolvió el"),
                    Columna("dias", "Días en poder"),
                    Columna("situacion", "Situación"),
                    Columna("estado_fisico", "Estado al devolver"),
                    Columna("obs_entrega", "Obs. de entrega"),
                    Columna("obs_devolucion", "Obs. de devolución"),
                ], filas_prestamos),
                Tabla("Observaciones y estado", [
                    Columna("fecha", "Fecha"),
                    Columna("momento", "Momento"),
                    Columna("usuario", "Persona"),
                    Columna("estado_fisico", "Estado del equipo"),
                    Columna("observacion", "Observación"),
                ], filas_observaciones),
                Tabla("Reservas", [
                    Columna("usuario", "Persona"),
                    Columna("fecha_reserva", "Reservada el"),
                    Columna("desde", "Desde"),
                    Columna("hasta", "Hasta"),
                    Columna("estado", "Estado"),
                ], filas_reservas),
            ],
        )
