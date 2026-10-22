from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date, timedelta
from http.cookiejar import CookieJar
import sqlite3
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPCookieProcessor
import test_account_flow as harness


class LoanFlowTests(harness.AccountFlowTests):
    test_registration_login_profiles_permissions_and_pdf = None

    def test_delivery_permissions_dates_atomicity_duplicates_and_persistence(self):
        def account(email, code):
            client = build_opener(HTTPCookieProcessor(CookieJar()))
            result = self.call(client, '/auth/register', dict(nombre=code, correo=email, codigo=code,
                              tipo='Estudiante', password='Password123!'))
            self.call(client, '/auth/login', dict(correo=email, password='Password123!'))
            return client, result['id']

        admin, aid = account('loan-admin@example.com', 'LOAN-ADMIN')
        second_admin, aid2 = account('loan-admin2@example.com', 'LOAN-ADMIN2')
        student, uid = account('loan-student@example.com', 'LOAN-STUDENT')
        other, _ = account('loan-other@example.com', 'LOAN-OTHER')
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE usuarios SET rol_id=(SELECT id FROM roles WHERE nombre='ADMIN') WHERE id IN (?,?)", (aid, aid2))
            db.commit()
        category = self.call(admin, '/categorias/', {'nombre':'Loan category'})
        equipment = self.call(admin, '/objetos/', dict(nombre='Loan laptop', categoria_id=category['id']))
        eid = equipment['id']
        today = date.today()
        body = dict(usuario_id=uid, objeto_id=eid, fecha_inicio=today.isoformat(), fecha_fin=(today+timedelta(days=2)).isoformat())
        reserva = self.call(student, '/reservas/', body)
        rid = reserva['id']

        def rejects(client, body, code):
            with self.assertRaises(HTTPError) as error:
                self.call(client, '/prestamos/', body)
            self.assertEqual(error.exception.code, code)

        rejects(build_opener(), {'reserva_id':rid}, 401)
        rejects(student, {'reserva_id':rid}, 403)
        rejects(admin, {'reserva_id':99999}, 404)
        rejects(admin, {'reserva_id':rid}, 409)  # Pending reservation.
        self.call(admin, f'/reservas/{rid}/confirmar', {})
        self.call(admin, f'/objetos/{eid}', {'estado_fisico':'DANHADO'}, 'PUT')
        rejects(admin, {'reserva_id':rid}, 409)
        self.assertEqual(self.call(admin, f'/reservas/{rid}')['estado'], 'CONFIRMADA')
        self.assertEqual(self.call(admin, '/prestamos/'), [])
        self.call(admin, f'/objetos/{eid}', {'estado_fisico':'BUENO', 'estado_disponibilidad':'DISPONIBLE'}, 'PUT')
        self.call(admin, f'/usuarios/{uid}/estado', {'estado':'SUSPENDIDO'}, 'PUT')
        rejects(admin, {'reserva_id':rid}, 400)
        self.call(admin, f'/usuarios/{uid}/estado', {'estado':'ACTIVO'}, 'PUT')

        def deliver(client):
            try: return 201, self.call(client, '/prestamos/', {'reserva_id':rid, 'observaciones':'USB + cargador'})
            except HTTPError as error: return error.code, None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(deliver, [admin, second_admin]))
        self.assertEqual(sorted(code for code, _ in results), [201, 409])
        loan = next(result for code, result in results if code == 201)
        self.assertEqual(loan['estado'], 'ACTIVO')
        self.assertEqual(loan['observaciones_entrega'], 'USB + cargador')
        self.assertEqual(loan['fecha_inicio'], today.isoformat())
        self.assertEqual(self.call(admin, f'/objetos/{eid}')['estado_disponibilidad'], 'PRESTADO')
        self.assertEqual(self.call(admin, f'/reservas/{rid}')['estado'], 'FINALIZADA')
        for method, body_change in [('PUT', {'estado_disponibilidad':'DISPONIBLE'}), ('DELETE', None)]:
            with self.assertRaises(HTTPError) as error:
                self.call(admin, f'/objetos/{eid}', body_change, method)
            self.assertEqual(error.exception.code, 409)
        rejects(admin, {'reserva_id':rid}, 409)
        self.assertEqual(len(self.call(student, '/prestamos/')), 1)
        self.assertEqual(self.call(other, f'/prestamos/?usuario_id={uid}'), [])
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM prestamos').fetchone()[0], 1)
            self.assertEqual(db.execute('SELECT reserva_id FROM prestamos').fetchone()[0], rid)

        # Future and expired confirmed reservations cannot be delivered.
        for offset in [5, 10]:
            obj = self.call(admin, '/objetos/', dict(nombre=f'Other {offset}', categoria_id=category['id']))
            r = self.call(student, '/reservas/', dict(body, objeto_id=obj['id'], fecha_inicio=(today+timedelta(days=offset)).isoformat(), fecha_fin=(today+timedelta(days=offset+1)).isoformat()))
            self.call(admin, f'/reservas/{r["id"]}/confirmar', {})
            if offset == 10:
                with closing(sqlite3.connect(self.db)) as db:
                    db.execute('UPDATE reservas SET fecha_inicio=?,fecha_fin=? WHERE id=?', ((today-timedelta(days=2)).isoformat(), (today-timedelta(days=1)).isoformat(), r['id']))
                    db.commit()
            rejects(admin, {'reserva_id':r['id']}, 400)
            self.assertEqual(self.call(admin, f'/objetos/{obj["id"]}')['estado_disponibilidad'], 'DISPONIBLE')
        # Overdue remains an open loan and is calculated from the existing domain entity.
        with closing(sqlite3.connect(self.db)) as db:
            db.execute('UPDATE prestamos SET fecha_inicio=?,fecha_devolucion_prevista=? WHERE id=?', ((today-timedelta(days=3)).isoformat(), (today-timedelta(days=1)).isoformat(), loan['id']))
            db.commit()
        self.assertEqual(self.call(student, '/prestamos/')[0]['estado'], 'VENCIDO')
