from backend.usuarios.presentation.auth_routes import administrador
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from pydantic import BaseModel, Field, ConfigDict
from backend.recursos.infraestructure.models import CategoriaModel
from sqlalchemy.orm import Session

import os
from pathlib import Path
from fastapi.responses import FileResponse

from backend.database import get_db
from backend.recursos.domain.enums import EstadoDeDisponibilidad, EstadoFisico
from backend.recursos.domain.objeto import Objeto
from backend.recursos.infraestructure.sql_objeto_repository import SqlObjetoRepository
from backend.shared.errors import DomainError, NotFoundError

router = APIRouter(prefix="/objetos", tags=["Objetos"])

# Carpeta de subida para imágenes
OBJETOS_DIR = Path(os.environ.get('OBJETOS_DIR', str(Path(__file__).resolve().parents[3] / 'uploads' / 'objetos')))
MAX_IMAGE_BYTES = 2 * 1024 * 1024  # 2MB


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
        "imagen_url": f"/objetos/{o.id}/imagen" if o.imagen_path else None,
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


# ---------- Endpoints de Imagen ----------

@router.put("/{id_objeto}/imagen", dependencies=[Depends(administrador)])
async def subir_imagen(id_objeto: int, imagen: UploadFile = File(...), db: Session = Depends(get_db)):
    repo = SqlObjetoRepository(db)
    obj = repo.buscar_por_id(id_objeto)
    if not obj:
        raise HTTPException(404, "Equipo no encontrado.")
    
    # Validar extensión
    ext = Path(imagen.filename).suffix.lower() if imagen.filename else ""
    if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
        raise HTTPException(400, "Solo se permiten imágenes JPG, PNG o WEBP.")
    
    contenido = await imagen.read()
    if len(contenido) > MAX_IMAGE_BYTES:
        raise HTTPException(413, "La imagen no debe superar los 2MB.")
    
    OBJETOS_DIR.mkdir(parents=True, exist_ok=True)
    ruta_archivo = OBJETOS_DIR / f"{id_objeto}{ext}"
    
    # Borrar imagen anterior si existe con otra extensión
    for f in OBJETOS_DIR.glob(f"{id_objeto}.*"):
        f.unlink()
        
    ruta_archivo.write_bytes(contenido)
    
    # Guardar en BD
    obj.imagen_path = ruta_archivo.name
    repo.guardar(obj)
    
    return {"mensaje": "Imagen actualizada correctamente."}


@router.get("/{id_objeto}/imagen")
def obtener_imagen(id_objeto: int, db: Session = Depends(get_db)):
    repo = SqlObjetoRepository(db)
    obj = repo.buscar_por_id(id_objeto)
    if not obj or not obj.imagen_path:
        raise HTTPException(404, "Imagen no encontrada.")
    
    ruta = OBJETOS_DIR / obj.imagen_path
    if not ruta.is_file():
        raise HTTPException(404, "Archivo de imagen no encontrado en el servidor.")
        
    return FileResponse(ruta)


# ---------- Endpoints de Detalle / Edición ----------

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
        # Borrar la imagen si existía
        for f in OBJETOS_DIR.glob(f"{id_objeto}.*"):
            f.unlink(missing_ok=True)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------- Utilidades ----------

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