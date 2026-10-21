from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.recursos.domain.categoria import Categoria
from backend.recursos.domain.categoria_repository import CategoriaRepository
from backend.recursos.infraestructure.models import CategoriaModel
from backend.shared.errors import NotFoundError


class SqlCategoriaRepository(CategoriaRepository):

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _a_dominio(m: CategoriaModel) -> Categoria:
        return Categoria(id_categoria=m.id, nombre=m.nombre,
                         descripcion=m.descripcion or "", activa=m.activa)

    def guardar(self, categoria: Categoria) -> Categoria:
        if categoria.id_categoria is None:
            modelo = CategoriaModel()
            self.db.add(modelo)
        else:
            modelo = self.db.get(CategoriaModel, categoria.id_categoria)
            if modelo is None:
                raise NotFoundError(f"Categoría {categoria.id_categoria} no existe.")
        modelo.nombre = categoria.nombre
        modelo.descripcion = categoria.descripcion
        modelo.activa = categoria.activa
        self.db.commit()
        self.db.refresh(modelo)
        return self._a_dominio(modelo)

    def buscar_por_id(self, id: int) -> Optional[Categoria]:
        modelo = self.db.get(CategoriaModel, id)
        return self._a_dominio(modelo) if modelo else None

    def buscar_por_nombre(self, nombre: str) -> Optional[Categoria]:
        modelo = self.db.execute(
            select(CategoriaModel).where(CategoriaModel.nombre == nombre.strip())
        ).scalars().first()
        return self._a_dominio(modelo) if modelo else None

    def listar(self) -> list[Categoria]:
        modelos = self.db.execute(select(CategoriaModel).order_by(CategoriaModel.id)).scalars().all()
        return [self._a_dominio(m) for m in modelos]
