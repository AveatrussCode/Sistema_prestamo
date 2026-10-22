"""Create a consistent local SQLite backup without stopping the application."""
from contextlib import closing
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.database import engine


def respaldar():
    if engine.dialect.name != 'sqlite' or not engine.url.database:
        raise SystemExit('Este respaldo está preparado para la base SQLite local.')
    source = Path(engine.url.database).resolve()
    if not source.is_file():
        raise SystemExit('No se encontró la base local. No se creará una base vacía.')
    folder = ROOT / 'backups'
    folder.mkdir(exist_ok=True)
    target = folder / f'sistema_prestamo_{datetime.now():%Y%m%d_%H%M%S_%f}.db'
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as original:
        if original.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise SystemExit('La base no pasó la comprobación de integridad.')
        with closing(sqlite3.connect(target)) as backup:
            original.backup(backup)
            if backup.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise SystemExit(f'El respaldo no pasó la comprobación: {target}')
    print(f'Respaldo verificado: {target}')


if __name__ == '__main__':
    respaldar()
