from backend.usuarios.presentation.auth_routes import administrador
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.recursos.domain.categoria import Categoria
from backend.recursos.infraestructure.sql_categoria_repository import SqlCategoriaRepository
from backend.shared.errors import DomainError

router = APIRouter(prefix="/categorias", tags=["Categorías"])


class CategoriaCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str = Field(default='', max_length=2000)


def _a_dict(c: Categoria) -> dict:
    return {"id": c.id_categoria, "nombre": c.nombre, "descripcion": c.descripcion}


@router.post("/", status_code=201, dependencies=[Depends(administrador)])
def crear_categoria(datos: CategoriaCreate, db: Session = Depends(get_db)):
    repo = SqlCategoriaRepository(db)
    try:
        if repo.buscar_por_nombre(datos.nombre):
            raise HTTPException(409, 'Ya existe una categoría con este nombre.')
        return _a_dict(repo.guardar(Categoria(id_categoria=0, nombre=datos.nombre, descripcion=datos.descripcion)))
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Ya existe una categoría con este nombre.')
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def listar_categorias(db: Session = Depends(get_db)):
    return [_a_dict(c) for c in SqlCategoriaRepository(db).listar()]
