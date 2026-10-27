"""Muestra la base SQLite en modo de solo lectura, sin credenciales.

Desde la raíz: python -X utf8 scripts/ver_bd.py
Para imprimir sin abrir navegador: agrega --sin-abrir.
"""
import argparse
from datetime import datetime
from html import escape
from pathlib import Path
import sqlite3
import sys
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.database import engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sin-abrir', action='store_true')
    args = parser.parse_args()
    if engine.url.get_backend_name() != 'sqlite':
        parser.error('Este visor está preparado para la base SQLite del proyecto.')
    path = Path(engine.url.database).resolve()
    sections = []
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as db:
        db.execute('PRAGMA query_only = ON')
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for table in tables:
            identifier = '"' + table.replace('"', '""') + '"'
            schema = db.execute(f'PRAGMA table_info({identifier})').fetchall()
            count = db.execute(f'SELECT COUNT(*) FROM {identifier}').fetchone()[0]
            print(f'{table}: {count} registros')
            columns = [r[1] for r in schema if r[1] not in {'password_hash', 'token_hash'}]
            selection = ', '.join('"' + c.replace('"', '""') + '"' for c in columns)
            rows = db.execute(f'SELECT {selection} FROM {identifier} LIMIT 50').fetchall() if columns else []
            structure = ''.join('<tr>' + ''.join(f'<td>{escape(str(v))}</td>' for v in (r[1], r[2], 'Sí' if r[5] else '', 'Sí' if r[3] else '')) + '</tr>' for r in schema)
            heads = ''.join(f'<th>{escape(c)}</th>' for c in columns)
            records = ''.join('<tr>' + ''.join(f'<td>{escape(str(v)) if v is not None else "<em>NULL</em>"}</td>' for v in row) + '</tr>' for row in rows)
            sections.append(f'<section><h2>{escape(table)} · {count} registros</h2><details><summary>Estructura de columnas</summary><table><tr><th>Columna</th><th>Tipo</th><th>Clave primaria</th><th>Obligatoria explícita</th></tr>{structure}</table></details><div class="scroll"><table><tr>{heads}</tr>{records}</table></div><p>Hasta 50 filas. Los hashes de contraseña y sesión se omiten.</p></section>')
    report = ROOT / 'artifacts' / 'base_datos_presentacion.html'
    report.parent.mkdir(exist_ok=True)
    report.write_text('<!doctype html><html lang="es"><meta charset="utf-8"><title>Base de datos EPCC</title><style>body{font:16px system-ui;margin:32px;background:#f4f6fa;color:#172336}section{background:white;padding:20px;margin:20px 0;border-radius:12px}table{border-collapse:collapse;font-size:14px}td,th{padding:10px;border:1px solid #ddd;text-align:left;white-space:nowrap}th{background:#e8eff8}.scroll{overflow:auto;margin-top:16px}p{color:#46566b}</style><h1>Base de datos del sistema de préstamos</h1><p>Lectura de ' + escape(str(path)) + ' · ' + datetime.now().isoformat(timespec='seconds') + '</p><p>Esta página es una fotografía de la base. Vuelve a ejecutar el comando después de registrar una operación. No modifica los datos. Contiene datos personales: úsala para tu demostración local.</p>' + ''.join(sections) + '</html>', encoding='utf-8')
    print(f'Vista: {report}')
    if not args.sin_abrir:
        webbrowser.open(report.as_uri())


if __name__ == '__main__':
    main()
