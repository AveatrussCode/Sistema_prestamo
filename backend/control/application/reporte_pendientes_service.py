"""Caso de uso: generar el reporte "Pendientes de devolución".

La aplicación decide QUÉ contiene el reporte. No sabe de SQL ni de HTTP:
pide los datos al repositorio (interfaz) y arma un Reporte.
"""
from backend.control.domain.pendiente_devolucion_repository import PendienteDevolucionRepository
from backend.control.domain.reporte import Columna, DatoResumen, Reporte, Tabla


class ReportePendientesService:

    def __init__(self, repo: PendienteDevolucionRepository):
        self._repo = repo

    def generar(self, solo_vencidos: bool = False) -> Reporte:
        pendientes = self._repo.listar_activos()
        vencidos = [p for p in pendientes if p.esta_vencido()]
        mostrados = vencidos if solo_vencidos else pendientes

        # Los más atrasados primero
        mostrados = sorted(mostrados, key=lambda p: p.dias_de_atraso(), reverse=True)

        filas = [{
            "usuario": p.usuario,
            "correo": p.correo,
            "equipo": p.equipo,
            "fecha_inicio": p.prestamo.fecha_inicio.isoformat(),
            "fecha_prevista": p.prestamo.fecha_devolucion_prevista.isoformat(),
            "dias_atraso": p.dias_de_atraso(),
            "situacion": "Vencido" if p.esta_vencido() else "En plazo",
        } for p in mostrados]

        columnas = [
            Columna("usuario", "Usuario"),
            Columna("correo", "Correo"),
            Columna("equipo", "Equipo"),
            Columna("fecha_inicio", "Prestado el"),
            Columna("fecha_prevista", "Debía devolver el"),
            Columna("dias_atraso", "Días de atraso"),
            Columna("situacion", "Situación"),
        ]
        return Reporte(
            titulo="Pendientes de devolución",
            resumen=[
                DatoResumen("Equipos sin devolver", len(pendientes)),
                DatoResumen("Vencidos", len(vencidos)),
                DatoResumen("En plazo", len(pendientes) - len(vencidos)),
            ],
            tablas=[Tabla("Equipos sin devolver", columnas, filas)],
        )
