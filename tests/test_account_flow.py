"""Run: python -m unittest discover -s tests -v (uses an isolated database)."""
from contextlib import closing
import json
import os
import sqlite3
import subprocess
import tempfile
import time
import unittest
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]

class AccountFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.db = Path(cls.directory.name) / 'test.db'
        env = dict(os.environ, DATABASE_URL=f'sqlite:///{cls.db.as_posix()}',
                   MATRICULAS_DIR=str(Path(cls.directory.name)/'pdfs'), PYTHONUTF8='1')
        cls.log = open(Path(cls.directory.name)/'server.log', 'w+')
        cls.server = subprocess.Popen(['python', '-X', 'utf8', '-m', 'uvicorn', 'main:app',
                                       '--host', '127.0.0.1', '--port', '8021'],
                                      cwd=ROOT, env=env, stdout=cls.log, stderr=cls.log)
        cls.base = 'http://127.0.0.1:8021'
        for _ in range(100):
            try:
                cls.call(build_opener(), '/')
                return
            except Exception:
                if cls.server.poll() is not None:
                    break
                time.sleep(.1)
        cls.server.terminate(); cls.server.wait(timeout=10)
        cls.log.seek(0)
        raise RuntimeError(cls.log.read())

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate(); cls.server.wait(timeout=10)
        cls.log.close(); cls.directory.cleanup()

    @classmethod
    def call(cls, client, path, body=None, method=None, raw=False):
        data = body if raw else json.dumps(body).encode() if body is not None else None
        request = Request(cls.base+path, data=data, method=method,
                          headers={'Content-Type': 'application/pdf' if raw else 'application/json'})
        with client.open(request, timeout=10) as response:
            data=response.read()
            return data if raw else json.loads(data)

    def test_registration_login_profiles_permissions_and_pdf(self):
        client = build_opener(HTTPCookieProcessor(CookieJar()))
        student = {'nombre': 'Test Student', 'correo': ' STUDENT@EXAMPLE.COM ',
                   'codigo': 'TEST-EST-1', 'tipo': 'Estudiante', 'password': 'Password123!'}
        result=self.call(client, '/auth/register', student)
        uid=result['id']
        with closing(sqlite3.connect(self.db)) as db:
            password_hash=db.execute('SELECT password_hash FROM cuentas WHERE usuario_id=?',(uid,)).fetchone()[0]
            self.assertNotEqual(password_hash, student['password'])
            self.assertNotIn(student['password'],password_hash)
        for change, expected in [({},409),({'correo':'other@example.com'},409),
                                  ({'tipo':'Administrativo'},422),({'password':'short'},422),
                                  ({'correo':'invalid'},422),({'rol_id':1},422),({'nombre':' '},422)]:
            with self.assertRaises(HTTPError) as error:
                self.call(client, '/auth/register', dict(student, **change))
            self.assertEqual(error.exception.code,expected)
        with self.assertRaises(HTTPError) as error:
            self.call(client, '/auth/login', {'correo':'student@example.com','password':'wrong'})
        self.assertEqual(error.exception.code,401)
        user=self.call(client,'/auth/login',{'correo':'student@example.com','password':student['password']})
        self.assertFalse(user['administrador'])
        self.assertEqual(user['tipo'],'estudiante')
        self.assertEqual(self.call(client,'/auth/me')['id'],uid)
        for path in ['/usuarios/', '/roles/']:
            with self.assertRaises(HTTPError) as error: self.call(client,path)
            self.assertEqual(error.exception.code,403)
        with self.assertRaises(HTTPError) as error:
            self.call(client,'/auth/me',{'nombre':'Escalation','administrador':True},'PUT')
        self.assertEqual(error.exception.code,422)
        updated=self.call(client,'/auth/me',{'nombre':'Updated Student','especialidad':''},'PUT')
        self.assertEqual(updated['nombre'],'Updated Student')
        pdf=b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF'
        self.call(client,f'/usuarios/{uid}/constancia-matricula',pdf,'PUT',raw=True)
        self.assertTrue(self.call(client,'/auth/me')['constancia_matricula'])
        self.assertEqual(self.call(client,f'/usuarios/{uid}/constancia-matricula',raw=True),pdf)
        with self.assertRaises(HTTPError) as error:
            self.call(client,f'/usuarios/{uid}/constancia-matricula',b'invalid','PUT',raw=True)
        self.assertEqual(error.exception.code,400)
        professor=build_opener(HTTPCookieProcessor(CookieJar()))
        data=dict(student,nombre='Test Professor',correo='prof@example.com',codigo='TEST-PROF-1',tipo='Profesor',especialidad='Software')
        self.call(professor,'/auth/register',data)
        teacher=self.call(professor,'/auth/login',{'correo':data['correo'],'password':data['password']})
        self.assertEqual(teacher['especialidad'],'Software')
        self.assertFalse(teacher['administrador'])
        with self.assertRaises(HTTPError) as error:
            self.call(professor,f'/usuarios/{uid}/constancia-matricula',raw=True)
        self.assertEqual(error.exception.code,403)
        with self.assertRaises(HTTPError) as error:
            self.call(professor,f'/usuarios/{teacher["id"]}/constancia-matricula',pdf,'PUT',raw=True)
        self.assertEqual(error.exception.code,400)
        with self.assertRaises(HTTPError) as error:
            self.call(professor,'/reservas/',{'usuario_id':uid,'objeto_id':1,'fecha_inicio':'2027-01-01','fecha_fin':'2027-01-02'})
        self.assertEqual(error.exception.code,403)
        self.call(client,'/auth/logout',{})
        with self.assertRaises(HTTPError) as error: self.call(client,'/auth/me')
        self.assertEqual(error.exception.code,401)
        self.call(professor,'/auth/logout',{})
        # Fixture: administrative access is provisioned outside public registration.
        with closing(sqlite3.connect(self.db)) as db:
            role=db.execute("SELECT id FROM roles WHERE nombre='ADMIN'").fetchone()[0]
            cursor=db.execute("INSERT INTO usuarios (nombre,correo_institucional,codigo_institucional,tipo,estado,credibilidad,rol_id) VALUES (?,?,?,?,?,?,?)",('Test Admin','admin@example.com','TEST-ADMIN','administrativo','ACTIVO',100,role))
            admin_id=cursor.lastrowid
            db.execute('INSERT INTO cuentas(usuario_id,password_hash) VALUES (?,?)',(admin_id,password_hash))
            db.commit()
        admin=build_opener(HTTPCookieProcessor(CookieJar()))
        account=self.call(admin,'/auth/login',{'correo':'admin@example.com','password':student['password']})
        self.assertTrue(account['administrador'])
        self.assertEqual(len(self.call(admin,'/usuarios/')),3)
        category = self.call(admin, '/categorias/', {'nombre': 'Test laptops'})
        with self.assertRaises(HTTPError) as error:
            self.call(admin, '/categorias/', {'nombre': 'Test laptops'})
        self.assertEqual(error.exception.code, 409)
        equipment = dict(nombre='Test laptop', descripcion='Inventory test', categoria_id=category['id'],
                         estado_fisico='BUENO', estado_disponibilidad='DISPONIBLE')
        for invalid, expected in [(dict(equipment, nombre='  '), 422), (dict(equipment, categoria_id=999999), 400)]:
            with self.assertRaises(HTTPError) as error:
                self.call(admin, '/objetos/', invalid)
            self.assertEqual(error.exception.code, expected)
        obj = self.call(admin, '/objetos/', equipment)
        changed = self.call(admin, f'/objetos/{obj["id"]}', dict(equipment, nombre='Edited laptop', estado_fisico='DANHADO'), 'PUT')
        self.assertEqual(changed['estado_disponibilidad'], 'NO_DISPONIBLE')
        self.assertEqual(self.call(admin, f'/objetos/{obj["id"]}')['nombre'], 'Edited laptop')
        with self.assertRaises(HTTPError) as error:
            self.call(admin, f'/objetos/{obj["id"]}', {'nombre':'  '}, 'PUT')
        self.assertEqual(error.exception.code, 422)
        self.call(admin, f'/objetos/{obj["id"]}', {'estado_disponibilidad':'DADO_DE_BAJA'}, 'PUT')
        self.assertEqual(self.call(admin, '/objetos/'), [])
        self.assertEqual(len(self.call(admin, '/objetos/?estado=DADO_DE_BAJA')), 1)
        for kind in ['Estudiante', 'Profesor']:
            basic = build_opener(HTTPCookieProcessor(CookieJar()))
            email = 'student@example.com' if kind == 'Estudiante' else 'prof@example.com'
            self.call(basic, '/auth/login', {'correo':email, 'password':student['password']})
            self.assertEqual(self.call(basic, f'/objetos/{obj["id"]}')['id'], obj['id'])
            for path, body, method in [('/objetos/', equipment, 'POST'), (f'/objetos/{obj["id"]}', equipment, 'PUT'), ('/categorias/', {'nombre':'Forbidden'}, 'POST')]:
                with self.assertRaises(HTTPError) as error:
                    self.call(basic, path, body, method)
                self.assertEqual(error.exception.code, 403)
            self.call(basic, '/auth/logout', {})
        for kind in ['Estudiante', 'Profesor', 'Administrativo']:
            payload = dict(nombre=f'Created {kind}', correo=f'{kind.lower()}@example.com',
                           codigo=f'CREATED-{kind}', tipo=kind, password='InitialPass123!')
            created = self.call(admin, '/usuarios/', payload)
            account_client = build_opener(HTTPCookieProcessor(CookieJar()))
            signed_in = self.call(account_client, '/auth/login',
                                  dict(correo=payload['correo'], password=payload['password']))
            self.assertEqual(signed_in['id'], created['id'])
            self.assertEqual(signed_in['administrador'], kind == 'Administrativo')
            with self.assertRaises(HTTPError) as error:
                self.call(admin, '/usuarios/', dict(payload, correo=f'duplicate-{payload["correo"]}'))
            self.assertEqual(error.exception.code, 409)
            self.call(admin, f'/usuarios/{created["id"]}/estado', {'estado':'SUSPENDIDO'}, 'PUT')
            with self.assertRaises(HTTPError) as error:
                self.call(account_client, '/auth/me')
            self.assertEqual(error.exception.code, 401)
            with self.assertRaises(HTTPError) as error:
                self.call(account_client, '/auth/login', dict(correo=payload['correo'], password=payload['password']))
            self.assertEqual(error.exception.code, 401)
            self.call(admin, f'/usuarios/{created["id"]}/estado', {'estado':'ACTIVO'}, 'PUT')
            self.call(account_client, '/auth/login', dict(correo=payload['correo'], password=payload['password']))
            self.call(account_client, '/auth/logout', {})
        for path in ['/usuarios/', '/roles/', '/objetos/', '/reservas/']:
            with self.assertRaises(HTTPError) as error:
                self.call(build_opener(), path)
            self.assertEqual(error.exception.code, 401)
        self.call(admin,'/reservas/procesar-vencidas',{})
        self.call(client,'/auth/login',{'correo':'student@example.com','password':student['password']})
        self.call(admin,f'/usuarios/{uid}',method='DELETE')
        with self.assertRaises(HTTPError) as error: self.call(client,'/auth/me')
        self.assertEqual(error.exception.code,401)
        with closing(sqlite3.connect(self.db)) as db:
            self.assertIsNone(db.execute('SELECT usuario_id FROM cuentas WHERE usuario_id=?',(uid,)).fetchone())
        self.assertFalse((Path(self.directory.name)/'pdfs'/f'{uid}.pdf').exists())
        self.call(admin,'/auth/logout',{})


if __name__ == '__main__':
    unittest.main()
