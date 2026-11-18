"""Caso de uso: generar el REPORTE POR PERIODO (cómo estuvo el sistema entre dos fechas).

Sirve igual para "un mes" (del día 1 al último) que para cualquier rango de fechas.
La aplicación decide QUÉ contiene el reporte. No sabe de SQL ni de HTTP:
pide los datos al repositorio (interfaz) y arma un Reporte.
"""
from collections import Counter
from datetime import date

from backend.control.application.etiquetas import ESTADO_FISICO, ESTADO_RESERVA, etiqueta, fecha
from backend.control.domain.periodo_reporte_repository import PeriodoReporteRepository
from backend.control.domain.reporte import Columna, DatoResumen, Reporte, Tabla
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.shared.errors import DomainError

MAX_DIAS = 366  # un año; evita pedir "toda la historia" de golpe


def _dmy(valor: date) -> str:
    return valor.strftime("%d/%m/%Y")


class ReportePeriodoService:

    def __init__(self, repo: PeriodoReporteRepository):
        self._repo = repo

    def generar(self, desde: date, hasta: date) -> Reporte:
        if hasta < desde:
            raise DomainError("La fecha final no puede ser anterior a la fecha inicial.")
        if (hasta - desde).days + 1 > MAX_DIAS:
            raise DomainError(f"El periodo no puede superar {MAX_DIAS} días.")

        entregados = self._repo.prestamos_entregados(desde, hasta)
        devueltos = self._repo.devoluciones(desde, hasta)
        reservas = self._repo.reservas(desde, hasta)

        con_retraso = [d for d in devueltos if d.devuelto_con_retraso()]
        danados = [d for d in devueltos if d.estado_fisico == "DANHADO"]
        sin_devolver = [p for p in entregados if p.prestamo.estado == EstadoPrestamo.ACTIVO]
        vencidos = [p for p in sin_devolver if p.prestamo.esta_vencido()]
        equipos = {p.prestamo.id_objeto for p in entregados}
        personas = {p.prestamo.id_usuario for p in entregados}

        # --- Tablas de resumen -------------------------------------------------------------
        por_estado = Counter(r.estado for r in reservas)
        filas_reservas_estado = [
            {"estado": etiqueta(ESTADO_RESERVA, k), "cantidad": por_estado[k]}
            for k in ESTADO_RESERVA if por_estado[k]
        ]
        # por si apareciera un estado que no está en las etiquetas
        filas_reservas_estado += [
            {"estado": k, "cantidad": v} for k, v in por_estado.items() if k not in ESTADO_RESERVA
        ]

        actividad: dict[date, dict[str, int]] = {}

        def sumar(dia: date, campo: str):
            actividad.setdefault(dia, {"prestamos": 0, "devoluciones": 0, "reservas": 0})[campo] += 1

        for p in entregados:
            sumar(p.prestamo.fecha_inicio, "prestamos")
        for d in devueltos:
            sumar(d.fecha_real() or d.prestamo.fecha_inicio, "devoluciones")
        for r in reservas:
            sumar(r.fecha_reserva, "reservas")
        filas_actividad = [
            {"dia": fecha(dia), **actividad[dia]} for dia in sorted(actividad)
        ]

        por_equipo = Counter()
        nombre_equipo: dict[int, str] = {}
        por_persona = Counter()
        nombre_persona: dict[int, str] = {}
        for p in entregados:
            por_equipo[p.prestamo.id_objeto] += 1
            nombre_equipo[p.prestamo.id_objeto] = p.equipo
            por_persona[p.prestamo.id_usuario] += 1
            nombre_persona[p.prestamo.id_usuario] = p.usuario
        filas_equipos = [
            {"equipo": nombre_equipo[k], "prestamos": v}
            for k, v in sorted(por_equipo.items(), key=lambda kv: (-kv[1], nombre_equipo[kv[0]].lower()))
        ]
        filas_personas = [
            {"usuario": nombre_persona[k], "prestamos": v}
            for k, v in sorted(por_persona.items(), key=lambda kv: (-kv[1], nombre_persona[kv[0]].lower()))
        ]

        # --- Listados detallados -----------------------------------------------------------
        filas_entregados = [{
            "usuario": p.usuario,
            "equipo": p.equipo,
            "fecha_inicio": fecha(p.prestamo.fecha_inicio),
            "fecha_prevista": fecha(p.prestamo.fecha_devolucion_prevista),
            "fecha_devolucion": fecha(p.fecha_real()),
            "situacion": p.situacion(),
            "obs_entrega": p.obs_entrega,
        } for p in entregados]

        filas_devoluciones = [{
            "usuario": d.usuario,
            "equipo": d.equipo,
            "fecha_devolucion": fecha(d.fecha_real()),
            "situacion": d.situacion(),
            "estado_fisico": etiqueta(ESTADO_FISICO, d.estado_fisico),
            "obs_devolucion": d.obs_devolucion,
        } for d in devueltos]

        filas_reservas = [{
            "usuario": r.usuario,
            "equipo": r.equipo,
            "fecha_reserva": fecha(r.fecha_reserva),
            "desde": fecha(r.fecha_inicio),
            "hasta": fecha(r.fecha_fin),
            "estado": etiqueta(ESTADO_RESERVA, r.estado),
        } for r in reservas]

        return Reporte(
            titulo=f"Reporte de actividad: {_dmy(desde)} al {_dmy(hasta)}",
            resumen=[
                DatoResumen("Préstamos entregados", len(entregados)),
                DatoResumen("Devoluciones registradas", len(devueltos)),
                DatoResumen("Devueltos con retraso", len(con_retraso)),
                DatoResumen("Devueltos dañados", len(danados)),
                DatoResumen("Entregados sin devolver", len(sin_devolver)),
                DatoResumen("De ellos, vencidos", len(vencidos)),
                DatoResumen("Equipos distintos prestados", len(equipos)),
                DatoResumen("Personas con préstamos", len(personas)),
                DatoResumen("Reservas realizadas", len(reservas)),
            ],
            tablas=[
                Tabla("Actividad por día", [
                    Columna("dia", "Día"),
                    Columna("prestamos", "Préstamos realizados"),
                    Columna("devoluciones", "Devoluciones de equipos"),
                    Columna("reservas", "Reservas realizadas"),
                ], filas_actividad),
                Tabla("Estado de reservas", [
                    Columna("estado", "Estado"),
                    Columna("cantidad", "Cantidad"),
                ], filas_reservas_estado),
                Tabla("Equipos más prestados", [
                    Columna("equipo", "Equipo"),
                    Columna("prestamos", "Préstamos"),
                ], filas_equipos),
                Tabla("Personas con más préstamos", [
                    Columna("usuario", "Persona"),
                    Columna("prestamos", "Préstamos"),
                ], filas_personas),
                Tabla("Préstamos entregados", [
                    Columna("usuario", "Persona"),
                    Columna("equipo", "Equipo"),
                    Columna("fecha_inicio", "Prestado el"),
                    Columna("fecha_prevista", "Debía devolver el"),
                    Columna("fecha_devolucion", "Devolvió el"),
                    Columna("situacion", "Situación"),
                    Columna("obs_entrega", "Obs. de entrega"),
                ], filas_entregados),
                Tabla("Devoluciones", [
                    Columna("usuario", "Persona"),
                    Columna("equipo", "Equipo"),
                    Columna("fecha_devolucion", "Devolvió el"),
                    Columna("situacion", "Situación"),
                    Columna("estado_fisico", "Estado al devolver"),
                    Columna("obs_devolucion", "Obs. de devolución"),
                ], filas_devoluciones),
                Tabla("Reservas", [
                    Columna("usuario", "Persona"),
                    Columna("equipo", "Equipo"),
                    Columna("fecha_reserva", "Reservada el"),
                    Columna("desde", "Desde"),
                    Columna("hasta", "Hasta"),
                    Columna("estado", "Estado"),
                ], filas_reservas),
            ],
        )
