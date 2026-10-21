from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.recursos.domain.categoria import Categoria
from backend.recursos.domain.categoria_repository import CategoriaRepository
from backend.recursos.infrastructure.models import CategoriaModel
from backend.shared.errors import NotFoundError


class SqlCategoriaRepository(CategoriaRepository):

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _a_dominio(m: CategoriaModel) -> Categoria:
        return Categoria(
            id_categoria=m.id,
            nombre=m.nombre,
            descripcion=m.descripcion or "",
        )

    def guardar(self, categoria: Categoria) -> Categoria:
        if categoria.id_categoria is None or categoria.id_categoria == 0:
            modelo = CategoriaModel()
            self.db.add(modelo)
        else:
            modelo = self.db.get(CategoriaModel, categoria.id_categoria)
            if modelo is None:
                raise NotFoundError(f"Categoría {categoria.id_categoria} no existe.")
        modelo.nombre = categoria.nombre
        modelo.descripcion = categoria.descripcion
        self.db.commit()
        self.db.refresh(modelo)
        return self._a_dominio(modelo)

    def buscar_por_id(self, id: int) -> Optional[Categoria]:
        m = self.db.get(CategoriaModel, id)
        return self._a_dominio(m) if m else None

    def buscar_por_nombre(self, nombre: str) -> Optional[Categoria]:
        m = self.db.execute(
            select(CategoriaModel).where(CategoriaModel.nombre == nombre)
        ).scalar_one_or_none()
        return self._a_dominio(m) if m else None

    def listar(self) -> list[Categoria]:
        return [self._a_dominio(m) for m in self.db.execute(select(CategoriaModel)).scalars().all()]