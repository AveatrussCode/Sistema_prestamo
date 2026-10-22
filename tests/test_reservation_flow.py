from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from http.cookiejar import CookieJar
import sqlite3
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPCookieProcessor
import test_account_flow as harness


class ReservationFlowTests(harness.AccountFlowTests):
    test_registration_login_profiles_permissions_and_pdf = None

    def test_reservations_dates_permissions_conflicts_and_transitions(self):
        def account(email, code):
            client = build_opener(HTTPCookieProcessor(CookieJar()))
            result = self.call(client, '/auth/register', dict(nombre=code, correo=email, codigo=code,
                              tipo='Estudiante', password='Password123!'))
            self.call(client, '/auth/login', dict(correo=email, password='Password123!'))
            return client, result['id']

        admin, aid = account('admin-res@example.com', 'ADMIN-RES')
        student, uid = account('student-res@example.com', 'STUDENT-RES')
        other, oid = account('other-res@example.com', 'OTHER-RES')
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE usuarios SET rol_id=(SELECT id FROM roles WHERE nombre='ADMIN') WHERE id=?", (aid,))
            db.commit()
        category = self.call(admin, '/categorias/', {'nombre':'Reserva equipos'})
        equipment = self.call(admin, '/objetos/', dict(nombre='Reserva laptop', categoria_id=category['id']))
        eid = equipment['id']
        start = date.today() + timedelta(days=5)
        end = start + timedelta(days=2)
        body = dict(usuario_id=uid, objeto_id=eid, fecha_inicio=start.isoformat(), fecha_fin=end.isoformat())

        def rejects(client, path, data, expected, method=None):
            with self.assertRaises(HTTPError) as error:
                self.call(client, path, data, method)
            self.assertEqual(error.exception.code, expected)
            self.assertIn('detail', error.exception.read().decode())

        rejects(student, '/reservas/', dict(body, fecha_inicio=(date.today()-timedelta(days=1)).isoformat()), 400)
        rejects(student, '/reservas/', dict(body, fecha_fin=(start-timedelta(days=1)).isoformat()), 400)
        rejects(student, '/reservas/', dict(body, objeto_id=999999), 404)
        rejects(student, '/reservas/', dict(body, usuario_id=oid), 403)
        damaged = self.call(admin, '/objetos/', dict(nombre='Damaged', categoria_id=category['id'], estado_fisico='DANHADO'))
        rejects(student, '/reservas/', dict(body, objeto_id=damaged['id']), 400)

        # Two independent clients compete for the same dates; SQLite must persist only one.
        def reserve(client_and_user):
            client, user = client_and_user
            try:
                return 201, self.call(client, '/reservas/', dict(body, usuario_id=user))
            except HTTPError as error:
                return error.code, None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, [(student, uid), (other, oid)]))
        self.assertEqual(sorted(status for status, _ in results), [201, 409])
        created = next(r for status, r in results if status == 201)
        owner = student if created['usuario_id'] == uid else other
        stranger = other if owner is student else student
        rid = created['id']
        self.assertEqual(created['estado'], 'PENDIENTE')
        self.assertEqual(self.call(stranger, '/reservas/'), [])
        self.assertEqual(len(self.call(owner, '/reservas/?usuario_id=999')), 1)
        rejects(stranger, f'/reservas/{rid}', None, 403)
        rejects(stranger, f'/reservas/{rid}/cancelar', {}, 403)
        rejects(owner, f'/reservas/{rid}/confirmar', {}, 403)
        rejects(owner, f'/reservas/{rid}/finalizar', {}, 403)
        rejects(owner, '/reservas/procesar-vencidas', {}, 403)
        rejects(admin, f'/reservas/{rid}/finalizar', {}, 400)
        rejects(student, '/reservas/', dict(body, fecha_inicio=end.isoformat(), fecha_fin=(end+timedelta(days=1)).isoformat()), 409)
        self.assertEqual(self.call(admin, f'/reservas/{rid}/confirmar', {})['estado'], 'CONFIRMADA')
        rejects(admin, f'/reservas/{rid}/confirmar', {}, 400)
        self.assertEqual(self.call(owner, f'/reservas/{rid}/cancelar', {})['estado'], 'CANCELADA')
        rejects(owner, f'/reservas/{rid}/cancelar', {}, 400)
        replacement = self.call(student, '/reservas/', body)
        self.call(admin, f'/reservas/{replacement["id"]}/confirmar', {})
        self.assertEqual(self.call(admin, f'/reservas/{replacement["id"]}/finalizar', {})['estado'], 'FINALIZADA')
        # A non-overlapping future period remains valid for the same equipment.
        later = dict(body, fecha_inicio=(end+timedelta(days=2)).isoformat(), fecha_fin=(end+timedelta(days=3)).isoformat())
        late = self.call(student, '/reservas/', later)
        self.call(admin, f'/objetos/{eid}', {'estado_fisico':'DANHADO'}, 'PUT')
        rejects(admin, f'/reservas/{late["id"]}/confirmar', {}, 400)
        self.call(admin, f'/objetos/{eid}', {'estado_fisico':'BUENO', 'estado_disponibilidad':'DISPONIBLE'}, 'PUT')
        self.call(admin, f'/usuarios/{uid}/estado', {'estado':'SUSPENDIDO'}, 'PUT')
        rejects(admin, f'/reservas/{late["id"]}/confirmar', {}, 400)
        self.call(admin, f'/usuarios/{uid}/estado', {'estado':'ACTIVO'}, 'PUT')
        with closing(sqlite3.connect(self.db)) as db:
            db.execute('UPDATE reservas SET fecha_inicio=?,fecha_fin=? WHERE id=?',
                       ((date.today()-timedelta(days=2)).isoformat(), (date.today()-timedelta(days=1)).isoformat(), late['id']))
            db.commit()
        rejects(admin, f'/reservas/{late["id"]}/confirmar', {}, 400)
        self.assertEqual(self.call(admin, '/reservas/procesar-vencidas', {})[0]['estado'], 'VENCIDA')
        self.assertEqual(self.call(admin, '/reservas/procesar-vencidas', {}), [])
