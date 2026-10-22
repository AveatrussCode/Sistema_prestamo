"""Read-only catalog smoke check: python -X utf8 artifacts/verify_catalog.py."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True)
    try:
        for width, email, admin in [(1440, 'ana.ejemplo@unsa.edu.pe', False), (390, 'ana.ejemplo@unsa.edu.pe', False), (1440, 'lucia.ejemplo@unsa.edu.pe', True), (390, 'lucia.ejemplo@unsa.edu.pe', True)]:
            context = browser.new_context(viewport={'width': width, 'height': 950})
            page = context.new_page()
            page.set_default_timeout(12000)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto('http://127.0.0.1:5173/')
            page.locator('#email').fill(email)
            page.locator('#password').fill('Epcc2026!')
            page.locator('.login-submit').click()
            page.get_by_role('button', name='Catálogo', exact=True).click()
            page.locator('.objeto-card').first.wait_for()
            assert page.locator('.objeto-card').count() == 6
            assert page.get_by_role('button', name='+ Registrar equipo', exact=True).count() == int(admin)
            page.screenshot(path=f'artifacts/catalogo-nuevo-{width}-{admin}.png', full_page=True)
            page.get_by_role('button', name='Laptops', exact=True).click()
            assert page.locator('.objeto-card').count() == 2
            search = page.get_by_role('searchbox', name='Buscar equipos')
            search.fill('lenovo')
            assert page.locator('.objeto-card').count() == 1
            search.fill('no-existe-xyz')
            page.get_by_role('heading', name='No encontramos ese equipo').wait_for()
            page.get_by_role('button', name='Ver todos los equipos', exact=True).click()
            assert page.locator('.objeto-card').count() == 6
            page.get_by_label('Filtrar disponibilidad').select_option('NO_DISPONIBLE')
            assert page.locator('.objeto-card').count() == 1
            assert page.locator('.objeto-card .btn-reservar').is_disabled()
            page.get_by_role('button', name='Limpiar filtros ×', exact=True).click()
            page.get_by_label('Ordenar por').select_option('recientes')
            assert page.locator('.objeto-card').count() == 6
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            if admin:
                page.get_by_label('Filtrar disponibilidad').select_option('DADO_DE_BAJA')
                page.get_by_role('heading', name='No encontramos ese equipo').wait_for()
                page.get_by_role('button', name='Ver todos los equipos', exact=True).click()
            page.locator('.objeto-card .btn-reservar:not(:disabled)').first.click()
            page.locator('.page-reservas').wait_for()
            assert not errors, errors
            print(f'{width}, admin={admin}: search, category, status, reset, sorting, reservation shortcut, responsive OK', flush=True)
            context.close()
    finally:
        browser.close()
