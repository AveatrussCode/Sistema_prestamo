"""Pruebas de los servicios de reportes (equipo, periodo y usuario) con repositorios FALSOS.

No necesitan base de datos ni servidor encendido. Se ejecutan desde la raíz del proyecto con:
    python -m unittest tests.test_report_services -v
(o simplemente:  python tests/test_report_services.py)
"""
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.control.application.reporte_equipo_service import ReporteEquipoService
from backend.control.application.reporte_periodo_service import ReportePeriodoService
from backend.control.application.reporte_usuario_service import ReporteUsuarioService
from backend.control.domain.equipo_reporte_repository import EquipoReporteRepository
from backend.control.domain.historial_usuario import DatosUsuario, PrestamoDeUsuario, ReservaDeUsuario
from backend.control.domain.periodo_reporte_repository import PeriodoReporteRepository
from backend.control.domain.registro_prestamo import DatosEquipo, RegistroPrestamo, RegistroReserva
from backend.control.domain.usuario_reporte_repository import UsuarioReporteRepository
from backend.prestamos.domain.Prestamo import Prestamo
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.shared.errors import DomainError, NotFoundError

HOY = date.today()


def d(dias: int) -> date:
    return HOY + timedelta(days=dias)


def registro(id_, usuario_id, usuario, equipo_id, equipo, inicio, prevista, real=None,
             estado=EstadoPrestamo.ACTIVO, fisico=None, obs_e="", obs_d=""):
    return RegistroPrestamo(
        prestamo=Prestamo(id_, usuario_id, equipo_id, inicio, prevista, real, estado),
        usuario=usuario, correo=f"{usuario.lower()}@unsa.edu.pe", equipo=equipo,
        estado_fisico=fisico, obs_entrega=obs_e, obs_devolucion=obs_d,
    )


# Historia del equipo 1 ("Laptop"): Ana la devolvió bien y a tiempo, Beto la devolvió tarde y dañada,
# Carla la tiene vencida y Dario canceló.
PRESTAMOS_LAPTOP = [
    registro(4, 4, "Dario", 1, "Laptop", d(-1), d(3), estado=EstadoPrestamo.CANCELADO),
    registro(3, 3, "Carla", 1, "Laptop", d(-10), d(-5), obs_e="Cargador incluido"),
    registro(2, 2, "Beto", 1, "Laptop", d(-30), d(-25), d(-22), EstadoPrestamo.DEVUELTO, "DANHADO",
             obs_d="Pantalla rota"),
    registro(1, 1, "Ana", 1, "Laptop", d(-60), d(-55), d(-56), EstadoPrestamo.DEVUELTO, "BUENO",
             obs_e="Con funda"),
]


class EquipoFalso(EquipoReporteRepository):
    def __init__(self, existe=True):
        self.existe = existe

    def datos_de(self, id_equipo):
        if not self.existe:
            return None
        return DatosEquipo(1, "Laptop", "", "Computo", "NO_DISPONIBLE", "DANHADO")

    def prestamos_de(self, id_equipo):
        return PRESTAMOS_LAPTOP

    def reservas_de(self, id_equipo):
        return [RegistroReserva(1, "Carla", "Laptop", d(-12), d(-10), d(-5), "FINALIZADA")]


class ReporteEquipoTests(unittest.TestCase):
    def setUp(self):
        self.reporte = ReporteEquipoService(EquipoFalso()).generar(1)
        self.resumen = {x.etiqueta: x.valor for x in self.reporte.resumen}
        self.tablas = {t.titulo: t for t in self.reporte.tablas}

    def test_resumen(self):
        self.assertEqual(self.reporte.titulo, "Reporte de equipo: Laptop")
        self.assertEqual(self.resumen["Disponibilidad actual"], "No disponible")
        self.assertEqual(self.resumen["Estado físico actual"], "Dañado")
        self.assertEqual(self.resumen["Veces prestado"], 3)          # el cancelado no cuenta
        self.assertEqual(self.resumen["Sin devolver"], 1)
        self.assertEqual(self.resumen["Personas distintas"], 3)
        self.assertEqual(self.resumen["Devuelto con retraso"], 1)
        self.assertEqual(self.resumen["Devuelto dañado"], 1)
        self.assertEqual(self.resumen["Reservas realizadas"], 1)
        # Ana 4 días (60->56), Beto 8 (30->22), Carla 10 (sigue prestado)
        self.assertEqual(self.resumen["Días en préstamo"], 4 + 8 + 10)

    def test_historial_incluye_quien_cuando_y_estado(self):
        filas = self.tablas["Historial de préstamos"].filas
        self.assertEqual([f["usuario"] for f in filas], ["Dario", "Carla", "Beto", "Ana"])
        beto = filas[2]
        self.assertEqual(beto["situacion"], "Devuelto con retraso")
        self.assertEqual(beto["estado_fisico"], "Dañado")
        self.assertEqual(beto["obs_devolucion"], "Pantalla rota")
        self.assertEqual(filas[1]["situacion"], "Vencido")
        self.assertEqual(filas[0]["situacion"], "Cancelado")
        self.assertIsNone(filas[0]["dias"])

    def test_observaciones_mas_reciente_primero(self):
        filas = self.tablas["Observaciones y estado"].filas
        self.assertEqual(
            [(f["momento"], f["usuario"]) for f in filas],
            [("Entrega", "Carla"), ("Devolución", "Beto"), ("Devolución", "Ana"), ("Entrega", "Ana")],
        )
        self.assertEqual(filas[1]["estado_fisico"], "Dañado")
        self.assertEqual(filas[1]["observacion"], "Pantalla rota")

    def test_reservas_con_etiqueta(self):
        self.assertEqual(self.tablas["Reservas"].filas[0]["estado"], "Finalizada")

    def test_equipo_inexistente(self):
        with self.assertRaises(NotFoundError):
            ReporteEquipoService(EquipoFalso(existe=False)).generar(99)


class PeriodoFalso(PeriodoReporteRepository):
    """Equipo 1 prestado 2 veces, equipo 2 una vez; una devolución tardía y dañada."""

    def prestamos_entregados(self, desde, hasta):
        return [
            registro(1, 1, "Ana", 1, "Laptop", d(-20), d(-15), d(-14), EstadoPrestamo.DEVUELTO, "DANHADO", obs_d="Rota"),
            registro(2, 2, "Beto", 1, "Laptop", d(-10), d(-5)),                       # vencido
            registro(3, 1, "Ana", 2, "Cámara", d(-3), d(5)),                          # en plazo
        ]

    def devoluciones(self, desde, hasta):
        return [self.prestamos_entregados(desde, hasta)[0]]

    def reservas(self, desde, hasta):
        return [
            RegistroReserva(1, "Ana", "Laptop", d(-22), d(-20), d(-15), "FINALIZADA"),
            RegistroReserva(2, "Ana", "Cámara", d(-4), d(-3), d(5), "CONFIRMADA"),
            RegistroReserva(3, "Beto", "Cámara", d(-4), d(10), d(12), "CANCELADA"),
        ]


class ReportePeriodoTests(unittest.TestCase):
    def setUp(self):
        self.reporte = ReportePeriodoService(PeriodoFalso()).generar(d(-30), d(0))
        self.resumen = {x.etiqueta: x.valor for x in self.reporte.resumen}
        self.tablas = {t.titulo: t for t in self.reporte.tablas}

    def test_resumen(self):
        self.assertEqual(self.resumen["Préstamos entregados"], 3)
        self.assertEqual(self.resumen["Devoluciones registradas"], 1)
        self.assertEqual(self.resumen["Devueltos con retraso"], 1)
        self.assertEqual(self.resumen["Devueltos dañados"], 1)
        self.assertEqual(self.resumen["Entregados sin devolver"], 2)
        self.assertEqual(self.resumen["De ellos, vencidos"], 1)
        self.assertEqual(self.resumen["Equipos distintos prestados"], 2)
        self.assertEqual(self.resumen["Personas con préstamos"], 2)
        self.assertEqual(self.resumen["Reservas realizadas"], 3)

    def test_titulo_con_fechas(self):
        self.assertIn(d(-30).strftime("%d/%m/%Y"), self.reporte.titulo)
        self.assertIn(d(0).strftime("%d/%m/%Y"), self.reporte.titulo)

    def test_rankings(self):
        self.assertEqual(self.tablas["Equipos más prestados"].filas,
                         [{"equipo": "Laptop", "prestamos": 2}, {"equipo": "Cámara", "prestamos": 1}])
        self.assertEqual(self.tablas["Personas con más préstamos"].filas[0], {"usuario": "Ana", "prestamos": 2})

    def test_reservas_por_estado(self):
        self.assertEqual(
            {f["estado"]: f["cantidad"] for f in self.tablas["Reservas por estado"].filas},
            {"Confirmada": 1, "Finalizada": 1, "Cancelada": 1},
        )

    def test_actividad_por_dia_ordenada_y_sin_dias_vacios(self):
        filas = self.tablas["Actividad por día"].filas
        dias = [f["dia"] for f in filas]
        self.assertEqual(dias, sorted(dias))
        self.assertTrue(all(f["prestamos"] + f["devoluciones"] + f["reservas"] > 0 for f in filas))
        self.assertEqual(sum(f["prestamos"] for f in filas), 3)
        self.assertEqual(sum(f["devoluciones"] for f in filas), 1)
        self.assertEqual(sum(f["reservas"] for f in filas), 3)

    def test_devoluciones_con_estado_y_observacion(self):
        fila = self.tablas["Devoluciones"].filas[0]
        self.assertEqual((fila["estado_fisico"], fila["obs_devolucion"], fila["situacion"]),
                         ("Dañado", "Rota", "Devuelto con retraso"))

    def test_rango_invalido(self):
        servicio = ReportePeriodoService(PeriodoFalso())
        with self.assertRaises(DomainError):
            servicio.generar(d(0), d(-1))
        with self.assertRaises(DomainError):
            servicio.generar(d(-400), d(0))

    def test_un_solo_dia_es_valido(self):
        ReportePeriodoService(PeriodoFalso()).generar(d(0), d(0))


class UsuarioFalso(UsuarioReporteRepository):
    def datos_de(self, id_usuario):
        if id_usuario != 1:
            return None
        return DatosUsuario(1, "Ana", "ana@unsa.edu.pe", "estudiante", "ACTIVO", 90.0)

    def prestamos_de(self, id_usuario):
        return [PrestamoDeUsuario(Prestamo(1, 1, 1, d(-5), d(-1), d(-2), EstadoPrestamo.DEVUELTO),
                                  "Laptop", "DANHADO", "", "Pantalla rota")]

    def reservas_de(self, id_usuario):
        return [ReservaDeUsuario(1, "Laptop", d(-5), d(-1), "FINALIZADA")]


class ReporteUsuarioTests(unittest.TestCase):
    def test_textos_legibles(self):
        reporte = ReporteUsuarioService(UsuarioFalso()).generar(1)
        resumen = {x.etiqueta: x.valor for x in reporte.resumen}
        self.assertEqual((resumen["Tipo"], resumen["Estado de la cuenta"]), ("Estudiante", "Activo"))
        self.assertEqual(resumen["Devueltos dañados"], 1)
        prestamo = reporte.tablas[0].filas[0]
        self.assertEqual((prestamo["estado_fisico"], prestamo["obs_devolucion"]), ("Dañado", "Pantalla rota"))
        self.assertEqual(reporte.tablas[1].filas[0]["estado"], "Finalizada")

    def test_usuario_inexistente(self):
        with self.assertRaises(NotFoundError):
            ReporteUsuarioService(UsuarioFalso()).generar(2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
