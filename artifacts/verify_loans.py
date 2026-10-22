"""Loan delivery UI smoke check using a disposable SQLite copy."""
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
    dbpath = Path(directory) / 'loans.db'
    with closing(sqlite3.connect(engine.url.database)) as source, closing(sqlite3.connect(dbpath)) as target:
        source.backup(target)
    with closing(sqlite3.connect(dbpath)) as db:
        uid = db.execute("SELECT id FROM usuarios WHERE correo_institucional='ana.ejemplo@unsa.edu.pe'").fetchone()[0]
        fixtures = []
        for name in ['Laptop Dell Latitude 5420', 'Laptop Lenovo ThinkPad E14']:
            eid = db.execute('SELECT id FROM objetos WHERE nombre=?', (name,)).fetchone()[0]
            cursor = db.execute('INSERT INTO reservas(usuario_id,objeto_id,fecha_reserva,fecha_inicio,fecha_fin,estado) VALUES (?,?,?,?,?,?)',
                                (uid, eid, date.today().isoformat(), date.today().isoformat(), (date.today()+timedelta(days=2)).isoformat(), 'CONFIRMADA'))
            fixtures.append((cursor.lastrowid, name))
        db.commit()
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
                    for width, (rid, name) in zip([1440, 390], fixtures):
                        def login(email):
                            context = browser.new_context(viewport={'width':width, 'height':950})
                            page = context.new_page()
                            page.set_default_timeout(12000)
                            page.route('http://127.0.0.1:8000/**', lambda r: r.continue_(url=r.request.url.replace(':8000', ':8022')))
                            page.goto('http://127.0.0.1:5173/')
                            page.locator('#email').fill(email)
                            page.locator('#password').fill('Epcc2026!')
                            page.locator('.login-submit').click()
                            page.get_by_role('button', name='Catálogo', exact=True).wait_for()
                            return context, page
                        context, page = login('lucia.ejemplo@unsa.edu.pe')
                        page.get_by_role('button', name='Reservas', exact=True).click()
                        page.locator(f'tr[data-reserva-id="{rid}"]').get_by_role('button', name='Entregar equipo', exact=True).click()
                        select = page.get_by_label('Reserva confirmada', exact=True)
                        select.wait_for()
                        assert select.input_value() == str(rid)
                        page.get_by_label('Observaciones de entrega').fill('Cargador y cable USB incluidos')
                        page.get_by_role('button', name='Revisar entrega', exact=True).click()
                        page.get_by_role('button', name='Volver', exact=True).click()
                        assert not page.locator('dialog').is_visible()
                        page.get_by_role('button', name='Revisar entrega', exact=True).click()
                        with page.expect_response(lambda r: '/prestamos/' in r.url and r.request.method == 'POST' and r.status == 201) as delivered:
                            page.get_by_role('button', name='Confirmar entrega', exact=True).click()
                        loan_id = delivered.value.json()['id']
                        row = page.locator(f'tr[data-prestamo-id="{loan_id}"]')
                        row.wait_for()
                        assert row.locator('.estado-activo').is_visible()
                        page.screenshot(path=f'artifacts/prestamos-{width}.png', full_page=True)
                        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                        page.reload()
                        page.get_by_role('button', name='Préstamos', exact=True).click()
                        page.locator(f'tr[data-prestamo-id="{loan_id}"]').wait_for()
                        page.get_by_role('button', name='Catálogo', exact=True).click()
                        card = page.locator('.objeto-card').filter(has_text=name)
                        card.locator('.status-prestado').wait_for()
                        assert card.locator('.btn-reservar').is_disabled()
                        context.close()
                        for email, owns in [('ana.ejemplo@unsa.edu.pe', True), ('carlos.ejemplo@unsa.edu.pe', False)]:
                            context, page = login(email)
                            page.get_by_role('button', name='Mis préstamos', exact=True).click()
                            page.locator('.loan-list').wait_for()
                            page.get_by_role('button', name='Actualizar', exact=True).wait_for(state='visible')
                            if owns:
                                page.locator(f'tr[data-prestamo-id="{loan_id}"]').wait_for()
                            else:
                                page.get_by_text('Todavía no hay préstamos registrados', exact=True).wait_for()
                            assert page.locator('.loan-delivery').count() == 0
                            context.close()
                        print(f'{width}: reservation shortcut, review, delivery, persisted loan, borrowed equipment and own-loan permissions OK', flush=True)
                finally:
                    browser.close()
        finally:
            server.terminate()
            server.wait(timeout=10)
