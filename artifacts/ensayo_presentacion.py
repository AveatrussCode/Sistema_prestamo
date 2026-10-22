"""End-to-end rehearsal with new accounts and equipment in a disposable DB copy.
Run from repository root: python -X utf8 artifacts/ensayo_presentacion.py
Requires playwright and an installed Microsoft Edge; frontend at 127.0.0.1:5173.
"""
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.database import engine

with tempfile.TemporaryDirectory() as directory:
    dbpath = Path(directory) / 'rehearsal.db'
    with closing(sqlite3.connect(engine.url.database)) as source, closing(sqlite3.connect(dbpath)) as target:
        source.backup(target)
    with open(Path(directory) / 'server.log', 'w+', encoding='utf-8') as log:
        server = subprocess.Popen([sys.executable, '-X', 'utf8', '-m', 'uvicorn', 'main:app', '--port', '8022'], cwd=ROOT, env=dict(os.environ, DATABASE_URL='sqlite:///' + dbpath.as_posix(), MATRICULAS_DIR=str(Path(directory)/'pdfs'), PYTHONUTF8='1'), stdout=log, stderr=log)
        try:
            for _ in range(80):
                try:
                    urlopen('http://127.0.0.1:8022/', timeout=1).close()
                    break
                except Exception:
                    if server.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read())
                    time.sleep(.1)
            with sync_playwright() as p:
                browser = p.chromium.launch(channel='msedge', headless=True, timeout=20000)
                try:
                    for width in [1440, 390]:
                        errors = []
                        def new_page():
                            context = browser.new_context(viewport={'width': width, 'height': 950}, locale='es-PE')
                            page = context.new_page()
                            page.set_default_timeout(12000)
                            page.on('pageerror', lambda error: errors.append(str(error)))
                            page.route('http://127.0.0.1:8000/**', lambda r: r.continue_(url=r.request.url.replace(':8000', ':8022')))
                            page.goto('http://127.0.0.1:5173/')
                            return context, page
                        student_context, student = new_page()
                        student.locator('.login-register-switch').click()
                        student.locator('.registro input[autocomplete="name"]').fill(f'Estudiante Ensayo {width}')
                        student.locator('.registro input[autocomplete="username"]').fill(f'ensayo{width}@unsa.edu.pe')
                        student.get_by_label('Código institucional').fill(f'ENSAYO-{width}')
                        student.locator('.registro input[autocomplete="new-password"]').nth(0).fill('Ensayo2026!')
                        student.locator('.registro input[autocomplete="new-password"]').nth(1).fill('Ensayo2026!')
                        student.locator('.registro .login-submit').click()
                        student.get_by_role('button', name='Mi perfil', exact=True).click()
                        student.get_by_label('Nombre completo').fill(f'Participante Ensayo {width}')
                        student.get_by_role('button', name='Guardar mi información', exact=True).click()
                        student.locator('.usuario-success').wait_for()
                        assert student.get_by_role('button', name='Usuarios', exact=True).count() == 0

                        admin_context, admin = new_page()
                        admin.locator('#email').fill('lucia.ejemplo@unsa.edu.pe')
                        admin.locator('#password').fill('Epcc2026!')
                        admin.locator('.login-submit').click()
                        admin.get_by_role('button', name='Catálogo', exact=True).click()
                        admin.get_by_role('button', name='+ Registrar equipo', exact=True).click()
                        form = admin.locator('.equipment-dialog')
                        name = f'Laptop de ensayo {width}'
                        form.get_by_label('Nombre del equipo').fill(name)
                        form.locator('textarea').fill('Equipo para ensayar la presentación completa')
                        form.get_by_role('button', name='+ Crear categoría', exact=True).click()
                        form.get_by_label('Nueva categoría', exact=True).fill(f'Ensayo {width}')
                        form.get_by_role('button', name='Crear categoría', exact=True).click()
                        form.locator('form > footer .btn').click()
                        admin.locator('.inventory-success').wait_for()

                        student.get_by_role('button', name='Catálogo', exact=True).click()
                        student.get_by_role('searchbox', name='Buscar equipos').fill(name)
                        card = student.locator('.objeto-card').filter(has_text=name)
                        card.get_by_role('button', name='Reservar equipo', exact=True).click()
                        student.get_by_label('Desde', exact=True).fill(date.today().isoformat())
                        student.get_by_label('Hasta', exact=True).fill((date.today()+timedelta(days=2)).isoformat())
                        with student.expect_response(lambda r: '/reservas/' in r.url and r.request.method == 'POST' and r.status == 201) as created:
                            student.get_by_role('button', name='Crear reserva', exact=True).click()
                        rid = created.value.json()['id']
                        student.locator(f'tr[data-reserva-id="{rid}"] .estado-pendiente').wait_for()
                        student.screenshot(path=str(ROOT/f'artifacts/ensayo-reserva-{width}.png'), full_page=True)

                        admin.get_by_role('button', name='Reservas', exact=True).click()
                        row = admin.locator(f'tr[data-reserva-id="{rid}"]')
                        row.get_by_role('button', name='Confirmar', exact=True).click()
                        row.locator('.estado-confirmada').wait_for()
                        row.get_by_role('button', name='Entregar equipo', exact=True).click()
                        admin.get_by_label('Observaciones de entrega').fill('Cargador incluido. Equipo revisado.')
                        admin.get_by_role('button', name='Revisar entrega', exact=True).click()
                        with admin.expect_response(lambda r: '/prestamos/' in r.url and r.request.method == 'POST' and r.status == 201) as delivered:
                            admin.get_by_role('button', name='Confirmar entrega', exact=True).click()
                        pid = delivered.value.json()['id']
                        loanrow = admin.locator(f'tr[data-prestamo-id="{pid}"]')
                        loanrow.locator('.estado-activo').wait_for()
                        student.get_by_role('button', name='Mis préstamos', exact=True).click()
                        student.locator(f'tr[data-prestamo-id="{pid}"] .estado-activo').wait_for()
                        assert student.get_by_role('button', name='Registrar devolución', exact=True).count() == 0

                        loanrow.get_by_role('button', name='Registrar devolución', exact=True).click()
                        return_form = admin.locator('.return-dialog')
                        damaged = width == 390
                        return_form.get_by_label('Estado físico al recibir', exact=True).select_option('DANHADO' if damaged else 'BUENO')
                        return_form.get_by_label('Observaciones de devolución').fill('Pantalla dañada, requiere revisión.' if damaged else 'Equipo y cargador recibidos en buen estado.')
                        return_form.get_by_role('button', name='Confirmar devolución', exact=True).click()
                        loanrow.locator('.estado-devuelto').wait_for()
                        loanrow.locator('summary').click()
                        admin.screenshot(path=str(ROOT/f'artifacts/ensayo-devolucion-{width}.png'), full_page=True)
                        assert admin.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        student.get_by_role('button', name='Actualizar', exact=True).click()
                        student.locator(f'tr[data-prestamo-id="{pid}"] .estado-devuelto').wait_for()
                        admin.get_by_role('button', name='Catálogo', exact=True).click()
                        admin.get_by_role('searchbox', name='Buscar equipos').fill(name)
                        admin.locator('.objeto-card').filter(has_text=name).locator('.status-no_disponible' if damaged else '.status-disponible').wait_for()
                        # Session persists across reloads and is revoked on logout.
                        student.reload()
                        student.get_by_role('button', name='Mis préstamos', exact=True).click()
                        student.locator(f'tr[data-prestamo-id="{pid}"] .estado-devuelto').wait_for()
                        # A failed logout is visible and can be retried without losing the session.
                        logout_url = 'http://127.0.0.1:8000/auth/logout'
                        student.route(logout_url, lambda r: r.abort())
                        student.locator('.logout-button').click()
                        student.get_by_role('alert').wait_for()
                        student.get_by_role('button', name='Mis préstamos', exact=True).wait_for()
                        student.unroute(logout_url)
                        student.locator('.logout-button').click()
                        student.locator('#email').wait_for()
                        student.reload()
                        student.locator('#email').wait_for()
                        assert not errors, errors
                        print(f'{width}: new account > profile > new category/equipment > reservation > confirmation > delivery > return > catalog > reload/logout OK', flush=True)
                        student_context.close()
                        admin_context.close()
                finally:
                    browser.close()
            # Reopen the database in another process to verify committed results.
            check = "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); assert c.execute('SELECT COUNT(*) FROM devoluciones').fetchone()[0]>=2; print('Database reopened: persisted returns OK')"
            subprocess.run([sys.executable, '-c', check, str(dbpath)], check=True)
        finally:
            server.terminate()
            server.wait(timeout=10)
