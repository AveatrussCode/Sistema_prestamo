"""Browser reservation workflow against a disposable SQLite copy."""
from contextlib import closing
from datetime import date, timedelta
from pathlib import Path
import os
import sqlite3
import subprocess
import tempfile
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from backend.database import engine

with tempfile.TemporaryDirectory() as directory:
    dbpath = Path(directory) / 'reservations.db'
    with closing(sqlite3.connect(engine.url.database)) as source, closing(sqlite3.connect(dbpath)) as target:
        source.backup(target)
    with open(Path(directory) / 'server.log', 'w+', encoding='utf-8') as log:
        server = subprocess.Popen(['python', '-X', 'utf8', '-m', 'uvicorn', 'main:app', '--port', '8022'], env=dict(os.environ, DATABASE_URL='sqlite:///' + dbpath.as_posix(), PYTHONUTF8='1'), stdout=log, stderr=log)
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
                    for index, width in enumerate([1440, 390]):
                        def login(email):
                            context = browser.new_context(viewport={'width': width, 'height': 950})
                            page = context.new_page()
                            page.set_default_timeout(12000)
                            page.route('http://127.0.0.1:8000/**', lambda r: r.continue_(url=r.request.url.replace(':8000', ':8022')))
                            page.goto('http://127.0.0.1:5173/')
                            page.locator('#email').fill(email)
                            page.locator('#password').fill('Epcc2026!')
                            page.locator('.login-submit').click()
                            page.get_by_role('button', name='Catálogo', exact=True).wait_for()
                            return context, page

                        student_context, student = login('ana.ejemplo@unsa.edu.pe')
                        student.get_by_role('button', name='Catálogo', exact=True).click()
                        card = student.locator('.objeto-card').filter(has_text='Laptop Dell Latitude 5420')
                        card.get_by_role('button', name='Reservar equipo', exact=True).click()
                        equipo = student.locator('.reservation-form select')
                        equipo.wait_for()
                        assert equipo.input_value() == '1'
                        assert student.get_by_role('button', name='Confirmar', exact=True).count() == 0
                        start = date.today() + timedelta(days=10 + 10 * index)
                        end = start + timedelta(days=2)
                        def dates(page):
                            page.get_by_label('Desde', exact=True).fill(start.isoformat())
                            page.get_by_label('Hasta', exact=True).fill(end.isoformat())
                        dates(student)
                        with student.expect_response(lambda response: '/reservas/' in response.url and response.request.method == 'POST' and response.status == 201) as saved:
                            student.get_by_role('button', name='Crear reserva', exact=True).click()
                        rid = str(saved.value.json()['id'])
                        row = student.locator(f'tr[data-reserva-id="{rid}"]')
                        row.locator('.estado-pendiente').wait_for()
                        dates(student)
                        student.get_by_role('button', name='Crear reserva', exact=True).click()
                        student.get_by_role('alert').filter(has_text='reservado').wait_for()
                        admin_context, admin = login('lucia.ejemplo@unsa.edu.pe')
                        admin.get_by_role('button', name='Reservas', exact=True).click()
                        adminrow = admin.locator(f'tr[data-reserva-id="{rid}"]')
                        adminrow.get_by_role('button', name='Confirmar', exact=True).click()
                        adminrow.locator('.estado-confirmada').wait_for()
                        student.get_by_role('button', name='Actualizar', exact=True).click()
                        row.locator('.estado-confirmada').wait_for()
                        student.screenshot(path=f'artifacts/reservas-{width}.png', full_page=True)
                        assert student.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        row.get_by_role('button', name='Cancelar', exact=True).click()
                        student.get_by_role('button', name='Conservar reserva', exact=True).click()
                        row.locator('.estado-confirmada').wait_for()
                        row.get_by_role('button', name='Cancelar', exact=True).click()
                        student.get_by_role('button', name='Sí, cancelar reserva', exact=True).click()
                        row.locator('.estado-cancelada').wait_for()
                        dates(student)
                        student.get_by_role('button', name='Crear reserva', exact=True).click()
                        student.locator('tr[data-reserva-id]').first.locator('.estado-pendiente').wait_for()
                        student.reload()
                        student.get_by_role('button', name='Mis reservas', exact=True).click()
                        student.locator('tr[data-reserva-id]').first.locator('.estado-pendiente').wait_for()
                        print(f'{width}: catalog selection, create, overlap error, admin confirm, cancel dialog, rebook and persistence OK', flush=True)
                        student_context.close()
                        admin_context.close()
                finally:
                    browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)
