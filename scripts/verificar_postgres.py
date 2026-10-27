"""Verifica el flujo en un esquema temporal PostgreSQL y lo elimina al terminar."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
import sys
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.database import Base, engine
from backend.usuarios.infraestructure.models import RolModel, EstudianteModel
from backend.usuarios.infraestructure.usuario_repository import UsuarioRepository
from backend.usuarios.presentation.auth_routes import CuentaModel, SesionModel
from backend.recursos.infraestructure.models import CategoriaModel, ObjetoModel
from backend.recursos.infraestructure.sql_objeto_repository import SqlObjetoRepository
from backend.prestamos.infraestructure.sql_reserva_repository import SqlReservaRepository
from backend.prestamos.application.reserva_service import ReservaService
from backend.prestamos.application.prestamo_service import PrestamoService
from backend.recursos.domain.enums import EstadoFisico
from backend.shared.errors import ConflictError


def main():
    if engine.dialect.name != 'postgresql':
        raise SystemExit('Esta comprobación requiere DATABASE_URL de PostgreSQL.')
    schema = 'prueba_epcc_' + uuid4().hex
    # Nombre generado internamente: nunca se elimina public ni un esquema del usuario.
    with engine.begin() as db:
        db.execute(text(f'CREATE SCHEMA "{schema}"'))
    temporary = create_engine(engine.url, connect_args={
        'options': '-csearch_path=' + schema, 'connect_timeout': 15})
    try:
        Base.metadata.create_all(temporary)
        with Session(temporary) as db:
            role = RolModel(nombre='USUARIO_BASICO', nivel='BAJO')
            user = EstudianteModel(nombre='Prueba temporal', correo_institucional='temporal@example.com',
                                   codigo_institucional='TEMPORAL', rol=role)
            category = CategoriaModel(nombre='Temporal')
            db.add_all([user, category])
            db.flush()
            equipment = ObjetoModel(nombre='Equipo temporal', categoria_id=category.id)
            db.add(equipment)
            db.commit()
            uid, oid = user.id, equipment.id

        def reserve(_):
            with Session(temporary) as db:
                service = ReservaService(SqlReservaRepository(db), SqlObjetoRepository(db), UsuarioRepository(db))
                try:
                    result = service.crear(uid, oid, date.today(), date.today() + timedelta(days=1))
                    return 'creada', result.id_reserva
                except ConflictError:
                    db.rollback()
                    return 'conflicto', None

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, range(2)))
        assert sorted(r[0] for r in results) == ['conflicto', 'creada'], results
        rid = next(r[1] for r in results if r[0] == 'creada')
        print('OK: dos reservas simultáneas, una creada y otra rechazada.')
        with Session(temporary) as db:
            service = ReservaService(SqlReservaRepository(db), SqlObjetoRepository(db), UsuarioRepository(db))
            service.confirmar(rid)
            loan = PrestamoService(db).entregar(rid, uid)
            pid = loan.id
            assert loan.estado.name == 'ACTIVO'
            print('OK: confirmación y entrega en PostgreSQL.')
            returned = PrestamoService(db).devolver(pid, uid, EstadoFisico.BUENO, 'Prueba temporal')
            assert returned.estado.name == 'DEVUELTO'
            db.expire_all()
            assert db.get(ObjetoModel, oid).estado_disponibilidad.name == 'DISPONIBLE'
            assert returned.devolucion is not None
            print('OK: devolución y disponibilidad del equipo.')
    finally:
        temporary.dispose()
        with engine.begin() as db:
            db.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        print('Esquema temporal eliminado; datos compartidos sin cambios.')


if __name__ == '__main__':
    main()
