from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
from backend.recursos.domain.objeto import Objeto
from backend.recursos.infraestructure.sql_objeto_repository import SqlObjetoRepository
from backend.shared.errors import DomainError, NotFoundError

router = APIRouter(prefix="/objetos", tags=["Objetos"])


# ---------- Esquemas ----------

class ObjetoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: str = ""
    categoria_id: int
    estado_fisico: EstadoFisico = EstadoFisico.BUENO


class ObjetoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    categoria_id: int | None = None
    estado_fisico: EstadoFisico | None = None
    estado_disponibilidad: EstadoDeDisponibilidad | None = None


def _a_dict(o: Objeto) -> dict:
    return {
        "id": o.id,
        "nombre": o.nombre,
        "descripcion": o.descripcion,
        "categoria_id": o.categoria_id,
        "estado_disponibilidad": o.estado_disponibilidad.value,
        "estado_fisico": o.estado_fisico.value,
    }


# ---------- Endpoints ----------

@router.post("/", status_code=201)
def crear_objeto(datos: ObjetoCreate, db: Session = Depends(get_db)):
    repo = SqlObjetoRepository(db)
    try:
        obj = Objeto(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            categoria_id=datos.categoria_id,
            estado_fisico=datos.estado_fisico,
        )
        return _a_dict(repo.guardar(obj))
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def listar_objetos(
    categoria_id: int | None = Query(None),
    estado: EstadoDeDisponibilidad | None = Query(None),
    busqueda: str | None = Query(None, description="Busca en nombre y descripción"),
    solo_disponibles: bool = Query(False, description="Solo objetos con estado DISPONIBLE"),
    db: Session = Depends(get_db),
):
    """Catálogo de objetos. Por defecto excluye DADO_DE_BAJA."""
    repo = SqlObjetoRepository(db)
    return [
        _a_dict(o)
        for o in repo.listar(
            categoria_id=categoria_id,
            estado=estado.value if estado else None,
            busqueda=busqueda,
            solo_disponibles=solo_disponibles,
        )
    ]


@router.get("/{id_objeto}")
def obtener_objeto(id_objeto: int, db: Session = Depends(get_db)):
    repo = SqlObjetoRepository(db)
    obj = repo.buscar_por_id(id_objeto)
    if obj is None:
        raise HTTPException(status_code=404, detail="Objeto no encontrado")
    return _a_dict(obj)


@router.put("/{id_objeto}")
def actualizar_objeto(id_objeto: int, datos: ObjetoUpdate, db: Session = Depends(get_db)):
    repo = SqlObjetoRepository(db)
    obj = repo.buscar_por_id(id_objeto)
    if obj is None:
        raise HTTPException(status_code=404, detail="Objeto no encontrado")

    if datos.nombre is not None:
        obj.nombre = datos.nombre
    if datos.descripcion is not None:
        obj.descripcion = datos.descripcion
    if datos.categoria_id is not None:
        obj.categoria_id = datos.categoria_id
    if datos.estado_fisico is not None:
        obj.estado_fisico = datos.estado_fisico
    if datos.estado_disponibilidad is not None:
        obj.estado_disponibilidad = datos.estado_disponibilidad

    try:
        return _a_dict(repo.guardar(obj))
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_objeto}", status_code=204)
def eliminar_objeto(id_objeto: int, db: Session = Depends(get_db)):
    repo = SqlObjetoRepository(db)
    try:
        repo.eliminar(id_objeto)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))