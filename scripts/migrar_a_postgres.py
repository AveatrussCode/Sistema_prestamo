"""Copia SQLite a PostgreSQL configurado en .env, sin borrar el origen.

Inspección: python -X utf8 scripts/migrar_a_postgres.py
Aplicar:   python -X utf8 scripts/migrar_a_postgres.py --aplicar
Requiere un destino vacío. Conserva IDs y contraseñas; no copia sesiones.
"""
import argparse
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

from sqlalchemy import MetaData, create_engine, func, inspect, select, text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.database import Base, engine
from backend.usuarios.infraestructure import models as usuarios
from backend.recursos.infraestructure import models as recursos
from backend.prestamos.infraestructure import models as prestamos
from backend.usuarios.presentation.auth_routes import CuentaModel, SesionModel


def migrar(source_path, destination, apply=False):
    source_path = Path(source_path).resolve()
    if not source_path.is_file():
        raise ValueError('No existe el archivo SQLite de origen.')
    if destination.dialect.name != 'postgresql':
        raise ValueError('El destino debe ser PostgreSQL. Configura DATABASE_URL en .env.')
    backup_folder = ROOT / 'backups'
    backup_folder.mkdir(exist_ok=True)
    snapshot = backup_folder / f'antes_neon_{datetime.now():%Y%m%d_%H%M%S_%f}.db'
    with closing(sqlite3.connect(source_path.as_uri() + '?mode=ro', uri=True)) as original:
        with closing(sqlite3.connect(snapshot)) as backup:
            original.backup(backup)
            if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise ValueError('El respaldo no pasó la comprobación de integridad.')
    print('Respaldo verificado:', snapshot)
    source = create_engine('sqlite:///' + snapshot.as_posix())
    try:
        metadata = MetaData()
        metadata.reflect(bind=source)
        tables = [t for t in Base.metadata.sorted_tables if t.name != 'sesiones']
        with source.connect() as src, destination.begin() as dst:
            if apply:
                dst.execute(text('SELECT pg_advisory_xact_lock(74202, 1)'))
            existing = set(inspect(dst).get_table_names())
            for table in Base.metadata.sorted_tables:
                if table.name in existing and dst.scalar(select(func.count()).select_from(table)):
                    raise ValueError('El destino contiene datos. No se mezcla ni sobrescribe: ' + table.name)
            rows_by_table = {}
            for table in tables:
                old = metadata.tables.get(table.name)
                rows = [dict(r) for r in src.execute(select(old)).mappings()] if old is not None else []
                rows_by_table[table.name] = rows
                print(f'{table.name}: {len(rows)} registros por copiar')
            if not apply:
                print('Inspección terminada. Para copiar, ejecuta de nuevo con --aplicar.')
                return
            Base.metadata.create_all(dst)
            for table in tables:
                rows = rows_by_table[table.name]
                if rows:
                    dst.execute(table.insert(), rows)
                actual = dst.scalar(select(func.count()).select_from(table))
                if actual != len(rows):
                    raise ValueError('Cantidad inesperada en ' + table.name)
                if 'id' in table.c and table.c.id.primary_key:
                    # Los nombres provienen de metadata del código, no de entrada externa.
                    dst.execute(text(
                        f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                        f'COALESCE((SELECT MAX(id) FROM "{table.name}"), 1), '
                        f'EXISTS(SELECT 1 FROM "{table.name}"))'))
            print('Copia verificada. No se copiaron sesiones: deben volver a iniciar sesión.')
    finally:
        source.dispose()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origen', type=Path, default=ROOT / 'sistema_prestamo.db')
    parser.add_argument('--aplicar', action='store_true')
    args = parser.parse_args()
    try:
        migrar(args.origen, engine, args.aplicar)
    except Exception as error:
        # No mostrar excepciones SQLAlchemy que puedan incluir parámetros sensibles.
        print('No se completó la migración:', str(error) if isinstance(error, ValueError) else type(error).__name__)
        sys.exit(1)
