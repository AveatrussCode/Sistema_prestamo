from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import date, timedelta
from http.cookiejar import CookieJar
import sqlite3
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPCookieProcessor
import test_account_flow as harness


class ReturnFlowTests(harness.AccountFlowTests):
    test_registration_login_profiles_permissions_and_pdf = None

    def test_returns_condition_permissions_atomicity_and_history(self):
        def account(email, code):
            client = build_opener(HTTPCookieProcessor(CookieJar()))
            result = self.call(client, '/auth/register', dict(nombre=code, correo=email, codigo=code,
                              tipo='Estudiante', password='Password123!'))
            self.call(client, '/auth/login', dict(correo=email, password='Password123!'))
            return client, result['id']
        admin, aid = account('return-admin@example.com', 'RETURN-ADMIN')
        second, aid2 = account('return-admin2@example.com', 'RETURN-ADMIN2')
        student, uid = account('return-student@example.com', 'RETURN-STUDENT')
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE usuarios SET rol_id=(SELECT id FROM roles WHERE nombre='ADMIN') WHERE id IN (?,?)", (aid, aid2))
            db.commit()
        category = self.call(admin, '/categorias/', {'nombre':'Return equipment'})
        today = date.today()

        def loan(name):
            equipment = self.call(admin, '/objetos/', dict(nombre=name, categoria_id=category['id']))
            body = dict(usuario_id=uid, objeto_id=equipment['id'], fecha_inicio=today.isoformat(), fecha_fin=(today+timedelta(days=2)).isoformat())
            r = self.call(student, '/reservas/', body)
            self.call(admin, f'/reservas/{r["id"]}/confirmar', {})
            return self.call(admin, '/prestamos/', {'reserva_id':r['id']}), equipment['id'], body

        def reject(client, pid, body, code):
            with self.assertRaises(HTTPError) as error:
                self.call(client, f'/prestamos/{pid}/devolucion', body)
            self.assertEqual(error.exception.code, code)

        active, eid, body = loan('Concurrent return laptop')
        pid = active['id']
        good = {'estado_fisico':'BUENO', 'observaciones':'Cargador recibido'}
        reject(build_opener(), pid, good, 401)
        reject(student, pid, good, 403)
        reject(admin, 999999, good, 404)
        reject(admin, pid, {'estado_fisico':'INVALID'}, 422)
        reject(admin, pid, dict(good, fecha_devolucion='2099-01-01'), 422)
        reject(admin, pid, {'estado_fisico':'DANHADO', 'observaciones':'   '}, 400)
        # A failure updating inventory must also undo the loan transition.
        with closing(sqlite3.connect(self.db)) as db:
            db.execute("UPDATE objetos SET estado_disponibilidad='NO_DISPONIBLE' WHERE id=?", (eid,))
            db.commit()
        reject(admin, pid, good, 409)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT estado FROM prestamos WHERE id=?', (pid,)).fetchone()[0], 'ACTIVO')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM devoluciones').fetchone()[0], 0)
            db.execute("UPDATE objetos SET estado_disponibilidad='PRESTADO' WHERE id=?", (eid,))
            db.commit()

        def give_back(client):
            try: return 201, self.call(client, f'/prestamos/{pid}/devolucion', good)
            except HTTPError as error: return error.code, None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(give_back, [admin, second]))
        self.assertEqual(sorted(code for code, _ in results), [201, 409])
        returned = next(r for code, r in results if code == 201)
        self.assertEqual(returned['estado'], 'DEVUELTO')
        self.assertEqual(returned['fecha_devolucion_real'], today.isoformat())
        self.assertFalse(returned['devolucion']['fuera_de_plazo'])
        self.assertEqual(returned['devolucion']['observaciones'], good['observaciones'])
        self.assertIn(returned['devolucion']['recibido_por'], [aid, aid2])
        self.assertEqual(self.call(admin, f'/objetos/{eid}')['estado_disponibilidad'], 'DISPONIBLE')
        reject(admin, pid, good, 409)
        # The item can be reserved and delivered again after a successful return.
        r = self.call(student, '/reservas/', body)
        self.call(admin, f'/reservas/{r["id"]}/confirmar', {})
        again = self.call(admin, '/prestamos/', {'reserva_id':r['id']})
        self.assertNotEqual(again['id'], pid)
        for state, late in [('REGULAR', False), ('DANHADO', True)]:
            active, object_id, reservation_body = loan(f'Return {state}')
            if late:
                with closing(sqlite3.connect(self.db)) as db:
                    db.execute('UPDATE prestamos SET fecha_inicio=?,fecha_devolucion_prevista=? WHERE id=?', ((today-timedelta(days=4)).isoformat(), (today-timedelta(days=1)).isoformat(), active['id']))
                    db.commit()
            result = self.call(admin, f'/prestamos/{active["id"]}/devolucion', {'estado_fisico':state, 'observaciones':'Estado documentado'})
            self.assertEqual(result['estado'], 'DEVUELTO')
            self.assertEqual(result['devolucion']['fuera_de_plazo'], late)
            item = self.call(admin, f'/objetos/{object_id}')
            self.assertEqual(item['estado_fisico'], state)
            self.assertEqual(item['estado_disponibilidad'], 'NO_DISPONIBLE' if state == 'DANHADO' else 'DISPONIBLE')
            if state == 'DANHADO':
                with self.assertRaises(HTTPError) as error:
                    self.call(student, '/reservas/', reservation_body)
                self.assertEqual(error.exception.code, 400)
        visible = self.call(student, '/prestamos/')
        self.assertEqual(len([p for p in visible if p['estado'] == 'DEVUELTO']), 3)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM devoluciones').fetchone()[0], 3)
