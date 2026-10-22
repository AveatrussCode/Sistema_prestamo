"""Browser smoke check on a disposable copy of the local database."""
from contextlib import closing
from pathlib import Path
import os
import sqlite3
import subprocess
import tempfile
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright
from backend.database import engine

def run():
    with tempfile.TemporaryDirectory() as directory:
        dbpath = Path(directory) / 'inventory.db'
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
                print('Isolated server ready', flush=True)
                with sync_playwright() as p:
                    browser = p.chromium.launch(channel='msedge', headless=True, timeout=20000)
                    try:
                        for width in [1440, 390]:
                            context = browser.new_context(viewport={'width': width, 'height': 900})
                            page = context.new_page()
                            page.set_default_timeout(10000)
                            page.route('http://127.0.0.1:8000/**', lambda r: r.continue_(url=r.request.url.replace(':8000', ':8022')))
                            page.goto('http://127.0.0.1:5173/')
                            page.locator('#email').fill('lucia.ejemplo@unsa.edu.pe')
                            page.locator('#password').fill('Epcc2026!')
                            page.locator('.login-submit').click()
                            page.get_by_role('button', name='Catálogo', exact=True).click()
                            page.get_by_role('button', name='+ Registrar equipo', exact=True).click()
                            dialog = page.locator('dialog')
                            dialog.get_by_label('Nombre del equipo').fill(f'UI equipo {width}')
                            dialog.get_by_role('button', name='+ Crear categoría', exact=True).click()
                            dialog.get_by_label('Nueva categoría', exact=True).fill(f'UI categoría {width}')
                            dialog.get_by_role('button', name='Crear categoría', exact=True).click()
                            dialog.locator('form > footer .btn').click()
                            page.locator('.inventory-success').wait_for()
                            page.get_by_role('button', name=f'Editar UI equipo {width}', exact=True).click()
                            dialog.get_by_label('Nombre del equipo').fill(f'UI editado {width}')
                            dialog.locator('.equipment-form-row select').first.select_option('DANHADO')
                            assert dialog.locator('.equipment-form-row select').nth(1).input_value() == 'NO_DISPONIBLE'
                            page.screenshot(path=f'artifacts/inventario-{width}.png', full_page=True)
                            dialog.locator('form > footer .btn').click()
                            page.locator('.inventory-success').wait_for()
                            page.reload()
                            page.get_by_role('button', name='Catálogo', exact=True).click()
                            card = page.locator('.objeto-card').filter(has_text=f'UI editado {width}')
                            card.wait_for()
                            assert card.locator('.btn-reservar').is_disabled()
                            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                            print(f'{width}: create category, register, edit and persistence OK', flush=True)
                            context.close()
                    finally:
                        browser.close()
            finally:
                server.terminate()
                server.wait(timeout=10)

if __name__ == '__main__':
    run()
