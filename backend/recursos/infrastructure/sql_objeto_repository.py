from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.recursos.domain.enums import EstadoDeDisponibilidad
from backend.recursos.domain.objeto import Objeto
from backend.recursos.domain.objeto_repository import ObjetoRepository
from backend.recursos.infraestructure.models import ObjetoModel
from backend.shared.errors import NotFoundError


class SqlObjetoRepository(ObjetoRepository):

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _a_dominio(m: ObjetoModel) -> Objeto:
        return Objeto(
            id_objeto=m.id, nombre=m.nombre, descripcion=m.descripcion or "",
            categoria_id=m.categoria_id, estado_disponibilidad=m.estado_disponibilidad,
            estado_fisico=m.estado_fisico,
        )

    def guardar(self, objeto: Objeto) -> Objeto:
        if objeto.id_objeto is None:
            modelo = ObjetoModel()
            self.db.add(modelo)
        else:
            modelo = self.db.get(ObjetoModel, objeto.id_objeto)
            if modelo is None:
                raise NotFoundError(f"Objeto {objeto.id_objeto} no existe.")
        modelo.nombre = objeto.nombre
        modelo.descripcion = objeto.descripcion
        modelo.categoria_id = objeto.categoria_id
        modelo.estado_disponibilidad = objeto.estado_disponibilidad
        modelo.estado_fisico = objeto.estado_fisico
        self.db.commit()
        self.db.refresh(modelo)
        return self._a_dominio(modelo)

    def buscar_por_id(self, id: int) -> Optional[Objeto]:
        modelo = self.db.get(ObjetoModel, id)
        return self._a_dominio(modelo) if modelo else None

    def listar(self, categoria_id: Optional[int] = None,
               solo_disponibles: bool = False) -> list[Objeto]:
        consulta = select(ObjetoModel).order_by(ObjetoModel.id)
        if categoria_id is not None:
            consulta = consulta.where(ObjetoModel.categoria_id == categoria_id)
        if solo_disponibles:
            consulta = consulta.where(
                ObjetoModel.estado_disponibilidad == EstadoDeDisponibilidad.DISPONIBLE)
        return [self._a_dominio(m) for m in self.db.execute(consulta).scalars().all()]
