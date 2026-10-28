from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
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
            id=m.id,
            nombre=m.nombre,
            descripcion=m.descripcion or "",
            categoria_id=m.categoria_id,
            estado_disponibilidad=m.estado_disponibilidad,
            estado_fisico=m.estado_fisico,
            imagen_path=m.imagen_path,
        )

    def guardar(self, objeto: Objeto) -> Objeto:
        if objeto.id is None:
            modelo = ObjetoModel()
            self.db.add(modelo)
        else:
            modelo = self.db.get(ObjetoModel, objeto.id)
            if modelo is None:
                raise NotFoundError(f"Objeto {objeto.id} no existe.")
        modelo.nombre = objeto.nombre
        modelo.descripcion = objeto.descripcion
        modelo.categoria_id = objeto.categoria_id
        modelo.estado_disponibilidad = objeto.estado_disponibilidad
        modelo.estado_fisico = objeto.estado_fisico
        modelo.imagen_path = objeto.imagen_path
        self.db.commit()
        self.db.refresh(modelo)
        return self._a_dominio(modelo)

    def buscar_por_id(self, id_objeto: int) -> Optional[Objeto]:
        modelo = self.db.get(ObjetoModel, id_objeto)
        return self._a_dominio(modelo) if modelo else None

    def listar(
        self,
        categoria_id: Optional[int] = None,
        estado: Optional[str] = None,
        busqueda: Optional[str] = None,
        solo_disponibles: bool = False,
    ) -> list[Objeto]:
        consulta = select(ObjetoModel).order_by(ObjetoModel.nombre)

        if categoria_id is not None:
            consulta = consulta.where(ObjetoModel.categoria_id == categoria_id)

        if estado is not None:
            consulta = consulta.where(ObjetoModel.estado_disponibilidad == estado)
        elif solo_disponibles:
            consulta = consulta.where(
                ObjetoModel.estado_disponibilidad == EstadoDeDisponibilidad.DISPONIBLE
            )
        else:
            # por defecto NO mostrar los dados de baja
            consulta = consulta.where(
                ObjetoModel.estado_disponibilidad != EstadoDeDisponibilidad.DADO_DE_BAJA
            )

        if busqueda:
            like = f"%{busqueda.strip()}%"
            consulta = consulta.where(
                or_(ObjetoModel.nombre.ilike(like), ObjetoModel.descripcion.ilike(like))
            )

        return [self._a_dominio(m) for m in self.db.execute(consulta).scalars().all()]

    def eliminar(self, id_objeto: int) -> None:
        modelo = self.db.get(ObjetoModel, id_objeto)
        if modelo is None:
            raise NotFoundError(f"Objeto {id_objeto} no existe.")
        self.db.delete(modelo)
        self.db.commit()