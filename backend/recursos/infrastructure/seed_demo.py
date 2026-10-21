"""Datos de prueba. Se ejecuta solo si el archivo .env tiene SEED_DEMO=true (ver main.py)."""
from sqlalchemy.orm import Session

from backend.recursos.infraestructure.models import CategoriaModel, ObjetoModel
from backend.usuarios.domain.usuario import EstadoUsuario
from backend.usuarios.infraestructure.models import (
    AdministrativoModel, EstudianteModel, UsuarioModel,
)


def seed_demo(db: Session) -> None:
    if db.query(UsuarioModel).count() == 0:
        db.add_all([
            EstudianteModel(nombre="Ana Torres", correo_institucional="ana.torres@univ.edu",
                            codigo_institucional="E001", credibilidad=100.0,
                            estado=EstadoUsuario.ACTIVO, carrera="Sistemas",
                            matricula="2024001", tipo="estudiante"),
            AdministrativoModel(nombre="Luis Rojas", correo_institucional="luis.rojas@univ.edu",
                                codigo_institucional="A001", credibilidad=100.0,
                                estado=EstadoUsuario.ACTIVO, area="Biblioteca",
                                cargo="Encargado", tipo="administrativo"),
        ])
        db.commit()

    if db.query(CategoriaModel).count() == 0:
        db.add_all([
            CategoriaModel(nombre="Laptops", descripcion="Equipos portátiles"),
            CategoriaModel(nombre="Libros", descripcion="Material bibliográfico"),
            CategoriaModel(nombre="Proyectores", descripcion="Proyectores multimedia"),
        ])
        db.commit()

    if db.query(ObjetoModel).count() == 0:
        categorias = {c.nombre: c.id for c in db.query(CategoriaModel).all()}
        db.add_all([
            ObjetoModel(nombre="Laptop Lenovo 01", descripcion="i5, 8 GB RAM",
                        categoria_id=categorias["Laptops"]),
            ObjetoModel(nombre="Laptop Lenovo 02", descripcion="i5, 8 GB RAM",
                        categoria_id=categorias["Laptops"]),
            ObjetoModel(nombre="Clean Code", descripcion="Robert C. Martin",
                        categoria_id=categorias["Libros"]),
            ObjetoModel(nombre="Proyector Epson", descripcion="HDMI + VGA",
                        categoria_id=categorias["Proyectores"]),
        ])
        db.commit()
