"""Carga datos de catálogo sin modificar registros existentes.
Ejecutar: python -m backend.recursos.infraestructure.seed_demo
"""
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.recursos.infraestructure.models import CategoriaModel, ObjetoModel
from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico

CATEGORIAS = {
    'Laptops': 'Equipos portátiles',
    'Proyectores': 'Presentaciones multimedia',
    'Electrónica': 'Kits de aprendizaje',
    'Cámaras web': 'Videoconferencias',
}
EQUIPOS = [
    ('Laptop Dell Latitude 5420', 'Core i5, 16 GB RAM, SSD 512 GB', 'Laptops', False),
    ('Laptop Lenovo ThinkPad E14', 'Ryzen 5, 16 GB RAM, SSD 256 GB', 'Laptops', False),
    ('Proyector Epson PowerLite', 'Proyector multimedia con conexión HDMI', 'Proyectores', False),
    ('Kit Arduino Uno', 'Placa, cable USB, protoboard y sensores', 'Electrónica', False),
    ('Cámara web Logitech C920', 'Videoconferencias Full HD con micrófono', 'Cámaras web', False),
    ('Proyector Epson de revisión', 'Pendiente de revisión técnica', 'Proyectores', True),
]

def seed_demo(db: Session) -> dict:
    """Agrega faltantes por nombre; conserva estados y datos existentes."""
    creados = {'categorias': 0, 'objetos': 0}
    try:
        for nombre, descripcion in CATEGORIAS.items():
            if not db.query(CategoriaModel).filter_by(nombre=nombre).first():
                db.add(CategoriaModel(nombre=nombre, descripcion=descripcion))
                creados['categorias'] += 1
        db.flush()
        categorias = {c.nombre: c.id for c in db.query(CategoriaModel).all()}
        for nombre, descripcion, categoria, revision in EQUIPOS:
            if db.query(ObjetoModel).filter_by(nombre=nombre).first():
                continue
            db.add(ObjetoModel(
                nombre=nombre, descripcion=descripcion, categoria_id=categorias[categoria],
                estado_disponibilidad=EstadoDeDisponibilidad.NO_DISPONIBLE if revision else EstadoDeDisponibilidad.DISPONIBLE,
                estado_fisico=EstadoFisico.REGULAR if revision else EstadoFisico.BUENO,
            ))
            creados['objetos'] += 1
        db.commit()
    except Exception:
        db.rollback()
        raise
    return creados

if __name__ == '__main__':
    with SessionLocal() as db:
        print('Registros creados:', seed_demo(db))
