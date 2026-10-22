from backend.usuarios.presentation.auth_routes import administrador
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from backend.recursos.infraestructure.models import CategoriaModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
from backend.recursos.domain.objeto import Objeto
from backend.recursos.infraestructure.sql_objeto_repository import SqlObjetoRepository
from backend.shared.errors import DomainError, NotFoundError

router = APIRouter(prefix="/objetos", tags=["Objetos"])


# ---------- Esquemas ----------

class ObjetoCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    nombre: str = Field(..., min_length=1, max_length=150)
    descripcion: str = Field(default='', max_length=2000)
    categoria_id: int = Field(gt=0)
    estado_fisico: EstadoFisico = EstadoFisico.BUENO
    estado_disponibilidad: EstadoDeDisponibilidad = EstadoDeDisponibilidad.DISPONIBLE


class ObjetoUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    nombre: str | None = Field(default=None, min_length=1, max_length=150)
    descripcion: str | None = Field(default=None, max_length=2000)
    categoria_id: int | None = Field(default=None, gt=0)
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

@router.post("/", status_code=201, dependencies=[Depends(administrador)])
def crear_objeto(datos: ObjetoCreate, db: Session = Depends(get_db)):
    validar_categoria(db, datos.categoria_id)
    repo = SqlObjetoRepository(db)
    try:
        obj = Objeto(
            nombre=datos.nombre,
            descripcion=datos.descripcion,
            categoria_id=datos.categoria_id,
            estado_fisico=datos.estado_fisico,
            estado_disponibilidad=datos.estado_disponibilidad,
        )
        if not obj.esta_operativo() and obj.esta_disponible():
            obj.marcar_no_disponible()
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


@router.put("/{id_objeto}", dependencies=[Depends(administrador)])
def actualizar_objeto(id_objeto: int, datos: ObjetoUpdate, db: Session = Depends(get_db)):
    repo = SqlObjetoRepository(db)
    obj = repo.buscar_por_id(id_objeto)
    if obj is None:
        raise HTTPException(status_code=404, detail="Objeto no encontrado")

    if datos.estado_disponibilidad is not None and datos.estado_disponibilidad != EstadoDeDisponibilidad.PRESTADO:
        comprobar_sin_prestamo_activo(db, id_objeto)
    if datos.nombre is not None:
        obj.nombre = datos.nombre
    if datos.descripcion is not None:
        obj.descripcion = datos.descripcion
    if datos.categoria_id is not None:
        validar_categoria(db, datos.categoria_id)
        obj.categoria_id = datos.categoria_id
    if datos.estado_fisico is not None:
        obj.estado_fisico = datos.estado_fisico
    if datos.estado_disponibilidad is not None:
        obj.estado_disponibilidad = datos.estado_disponibilidad
    if not obj.esta_operativo() and obj.esta_disponible():
        obj.marcar_no_disponible()

    try:
        return _a_dict(repo.guardar(obj))
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_objeto}", status_code=204, dependencies=[Depends(administrador)])
def eliminar_objeto(id_objeto: int, db: Session = Depends(get_db)):
    comprobar_sin_prestamo_activo(db, id_objeto)
    repo = SqlObjetoRepository(db)
    try:
        repo.eliminar(id_objeto)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


def validar_categoria(db: Session, categoria_id: int):
    categoria = db.get(CategoriaModel, categoria_id)
    if categoria is None:
        raise HTTPException(400, 'Selecciona una categoría existente.')
    if not categoria.activa:
        raise HTTPException(400, 'La categoría está desactivada.')


def comprobar_sin_prestamo_activo(db: Session, objeto_id: int):
    from backend.prestamos.infraestructure.models import PrestamoModel
    from backend.prestamos.domain.enums import EstadoPrestamo
    if db.query(PrestamoModel).filter_by(objeto_id=objeto_id, estado=EstadoPrestamo.ACTIVO).first():
        raise HTTPException(409, 'El equipo tiene un préstamo activo. Registra su devolución antes de cambiar su disponibilidad o eliminarlo.')
