from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.recursos.application.objeto_service import ObjetoService
from backend.recursos.domain.categoria import Categoria
from backend.recursos.domain.enums import EstadoFisico
from backend.recursos.domain.objeto import Objeto
from backend.recursos.infraestructure.sql_categoria_repository import SqlCategoriaRepository
from backend.recursos.infraestructure.sql_objeto_repository import SqlObjetoRepository
from backend.shared.errors import ConflictError

router = APIRouter(prefix="/objetos", tags=["Objetos"])
categoria_router = APIRouter(prefix="/categorias", tags=["Categorías"])


# ---------- Esquemas de entrada ----------

class ObjetoCreate(BaseModel):
    nombre: str
    descripcion: str = ""
    categoria_id: int


class EstadoFisicoRequest(BaseModel):
    estado: EstadoFisico


class CategoriaCreate(BaseModel):
    nombre: str
    descripcion: str = ""


# ---------- Armado del servicio ----------

def get_objeto_service(db: Session = Depends(get_db)) -> ObjetoService:
    return ObjetoService(SqlObjetoRepository(db), SqlCategoriaRepository(db))


def _objeto_a_dict(o: Objeto) -> dict:
    # Mismo formato que espera frontend/src/api/objetos.ts
    return {
        "id": o.id_objeto,
        "nombre": o.nombre,
        "descripcion": o.descripcion,
        "categoria_id": o.categoria_id,
        "estado_disponibilidad": o.estado_disponibilidad.value,
        "estado_fisico": o.estado_fisico.value,
    }


def _categoria_a_dict(c: Categoria) -> dict:
    return {"id": c.id_categoria, "nombre": c.nombre,
            "descripcion": c.descripcion, "activa": c.activa}


# ---------- Objetos (RF05-RF10) ----------

@router.get("/")
def listar_objetos(categoria_id: int | None = Query(None), solo_disponibles: bool = Query(False),
                   servicio: ObjetoService = Depends(get_objeto_service)):
    """RF05 - Visualización del inventario / RF09 - Consulta de disponibilidad."""
    return [_objeto_a_dict(o) for o in servicio.listar_objetos(categoria_id, solo_disponibles)]


@router.post("/", status_code=201)
def registrar_objeto(datos: ObjetoCreate, servicio: ObjetoService = Depends(get_objeto_service)):
    """RF06 - Registro de objetos."""
    return _objeto_a_dict(servicio.registrar_objeto(datos.nombre, datos.descripcion, datos.categoria_id))


@router.get("/{id_objeto}")
def obtener_objeto(id_objeto: int, servicio: ObjetoService = Depends(get_objeto_service)):
    return _objeto_a_dict(servicio.obtener_objeto(id_objeto))


@router.post("/{id_objeto}/estado-fisico")
def actualizar_estado_fisico(id_objeto: int, datos: EstadoFisicoRequest,
                             servicio: ObjetoService = Depends(get_objeto_service)):
    """RF10 - Registro del estado físico."""
    return _objeto_a_dict(servicio.actualizar_estado_fisico(id_objeto, datos.estado))


@router.post("/{id_objeto}/baja")
def dar_de_baja(id_objeto: int, servicio: ObjetoService = Depends(get_objeto_service)):
    """RF08 - Baja de objetos."""
    return _objeto_a_dict(servicio.dar_de_baja(id_objeto))


# ---------- Categorías ----------

@categoria_router.get("/")
def listar_categorias(db: Session = Depends(get_db)):
    return [_categoria_a_dict(c) for c in SqlCategoriaRepository(db).listar()]


@categoria_router.post("/", status_code=201)
def crear_categoria(datos: CategoriaCreate, db: Session = Depends(get_db)):
    repo = SqlCategoriaRepository(db)
    if repo.buscar_por_nombre(datos.nombre) is not None:
        raise ConflictError(f"Ya existe la categoría '{datos.nombre.strip()}'.")
    return _categoria_a_dict(repo.guardar(Categoria(nombre=datos.nombre.strip(),
                                                    descripcion=datos.descripcion)))
