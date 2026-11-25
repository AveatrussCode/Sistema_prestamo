"""Pruebas del sistema de credibilidad con SQLite en memoria. Ejecutar: python -m unittest tests.test_credibilidad -v"""
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.control.application.credibilidad_service import CredibilidadService
from backend.control.domain import politica_credibilidad as P
from backend.control.infraestructure.models import MovimientoCredibilidadModel
from backend.control.infraestructure.sql_credibilidad_repository import SqlCredibilidadRepository
from backend.database import Base
from backend.prestamos.domain.enums import EstadoPrestamo
from backend.prestamos.domain.reserva import EstadoReserva
from backend.prestamos.infraestructure.models import PrestamoModel, ReservaModel
from backend.recursos.domain.enums import EstadoFisico
from backend.recursos.infraestructure.models import CategoriaModel, ObjetoModel  # noqa: F401
from backend.shared.errors import DomainError
from backend.usuarios.infraestructure.models import EstudianteModel, ProfesorModel

HOY = date.today()


class PoliticaTest(unittest.TestCase):
    def test_niveles_y_ejemplo_del_diseno(self):
        self.assertEqual(P.nivel(50, "estudiante"), P.Nivel.ESTANDAR)
        self.assertEqual(P.nivel(139, "profesor"), P.Nivel.ESTANDAR)
        self.assertEqual(P.nivel(140, "profesor"), P.Nivel.CONFIABLE)
        v = 50 + P.puntos_devolucion_tardia(2, "estudiante") + P.puntos(P.TipoMovimiento.EQUIPO_DANADO, "estudiante")
        self.assertEqual((v, P.nivel(v, "estudiante")), (29, P.Nivel.EN_OBSERVACION))

    def test_subida_automatica_tiene_techo(self):
        self.assertEqual(P.limitar_subida(68, 3, "estudiante"), 1)
        self.assertEqual(P.limitar_subida(70, 3, "estudiante"), 0)
        self.assertEqual(P.limitar_subida(70, -5, "estudiante"), -5)


class ServicioTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()
        self.est = EstudianteModel(nombre="Ana", correo_institucional="a@x", codigo_institucional="1",
                                   tipo="estudiante", credibilidad=50)
        self.prof = ProfesorModel(nombre="Luis", correo_institucional="l@x", codigo_institucional="2",
                                  tipo="profesor", credibilidad=100)
        self.db.add_all([self.est, self.prof]); self.db.commit()
        self.srv = CredibilidadService(SqlCredibilidadRepository(self.db))

    def devolver(self, usuario, prestamo_id, inicio, prevista, real, fisico=EstadoFisico.BUENO):
        self.srv.registrar_devolucion(usuario.id, prestamo_id, inicio, prevista, real, fisico)
        self.db.refresh(usuario)

    def test_tarde_y_danado_bajan_y_registran(self):
        self.devolver(self.est, 1, HOY - timedelta(days=5), HOY - timedelta(days=2), HOY, EstadoFisico.DANHADO)
        self.assertEqual(self.est.credibilidad, 50 - 6 - 15)
        tipos = {m.tipo for m in self.srv.resumen(self.est.id).movimientos}
        self.assertEqual(tipos, {P.TipoMovimiento.DEVOLUCION_TARDIA, P.TipoMovimiento.EQUIPO_DANADO})

    def test_personal_pierde_el_doble(self):
        self.devolver(self.prof, 1, HOY - timedelta(days=5), HOY, HOY, EstadoFisico.DANHADO)
        self.assertEqual(self.prof.credibilidad, 100 - 30)

    def test_bono_solo_si_dura_un_dia_y_con_tope_semanal(self):
        self.devolver(self.est, 1, HOY, HOY, HOY)                                   # mismo día: sin bono
        self.assertEqual(self.est.credibilidad, 50)
        for i in range(2, 6):                                                        # 4 limpias: +3 +3 y luego tope (+6/semana)
            self.devolver(self.est, i, HOY - timedelta(days=2), HOY, HOY)
        self.assertEqual(self.est.credibilidad, 56)

    def test_subida_automatica_no_pasa_de_69(self):
        self.est.credibilidad = 68; self.db.commit()
        self.devolver(self.est, 1, HOY - timedelta(days=2), HOY, HOY)
        self.assertEqual(self.est.credibilidad, 69)
        self.devolver(self.est, 2, HOY - timedelta(days=2), HOY, HOY)                # ya no sube más
        self.assertEqual(self.est.credibilidad, 69)

    def test_ajuste_manual_si_puede_pasar_de_69_y_valida_el_tope(self):
        self.srv.ajustar(self.est.id, 99, "Buen historial", valor=85)
        self.db.refresh(self.est); self.assertEqual(self.est.credibilidad, 85)
        with self.assertRaises(DomainError): self.srv.ajustar(self.est.id, 99, "x", valor=150)
        with self.assertRaises(DomainError): self.srv.ajustar(self.est.id, 99, " ", valor=60)

    def test_anular_devuelve_los_puntos_una_sola_vez(self):
        self.devolver(self.est, 1, HOY - timedelta(days=5), HOY - timedelta(days=2), HOY)   # -6
        sancion = self.srv.resumen(self.est.id).movimientos[0]
        self.srv.anular(sancion.id, 99, "Cerrado por feriado"); self.db.refresh(self.est)
        self.assertEqual(self.est.credibilidad, 50)
        with self.assertRaises(DomainError): self.srv.anular(sancion.id, 99, "otra vez")

    def test_no_recogida_no_se_duplica(self):
        self.srv.sancionar_no_recogida(self.est.id, 7)
        self.assertEqual(self.db.get(type(self.est), self.est.id).credibilidad, 45)

    def test_reglas_al_reservar(self):
        v = self.srv.validar_reserva
        v(self.est.id, HOY, HOY + timedelta(days=1), HOY)                            # 2 días, estándar: ok
        with self.assertRaisesRegex(DomainError, "máximo es 2"): v(self.est.id, HOY, HOY + timedelta(days=2), HOY)
        with self.assertRaisesRegex(DomainError, "anticipación"): v(self.est.id, HOY + timedelta(days=8), HOY + timedelta(days=8), HOY)
        self.db.add(ReservaModel(usuario_id=self.est.id, objeto_id=1, fecha_reserva=HOY, fecha_inicio=HOY,
                                 fecha_fin=HOY, estado=EstadoReserva.PENDIENTE)); self.db.commit()
        with self.assertRaisesRegex(DomainError, "1 equipo"): v(self.est.id, HOY, HOY, HOY)
        self.est.credibilidad = 10; self.db.commit()
        with self.assertRaisesRegex(DomainError, "no puedes reservar"): v(self.est.id, HOY, HOY, HOY)

    def test_prestamo_vencido_bloquea(self):
        self.db.add(PrestamoModel(reserva_id=1, usuario_id=self.prof.id, objeto_id=1, entregado_por=1,
                                  usuario_nombre="Luis", objeto_nombre="Cable", fecha_inicio=HOY - timedelta(days=9),
                                  fecha_devolucion_prevista=HOY - timedelta(days=1), estado=EstadoPrestamo.ACTIVO)); self.db.commit()
        with self.assertRaisesRegex(DomainError, "vencido"): self.srv.validar_reserva(self.prof.id, HOY, HOY, HOY)
        with self.assertRaisesRegex(DomainError, "vencido"): self.srv.validar_entrega(self.prof.id, HOY)


if __name__ == "__main__":
    unittest.main()
