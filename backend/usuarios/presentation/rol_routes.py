from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.usuarios.infraestructure.usuario_repository import RolRepository


router = APIRouter(prefix="/roles", tags=["Roles"])


@router.get("/")
def listar_roles(db: Session = Depends(get_db)):
    """Lista todos los roles disponibles en el sistema."""
    repo = RolRepository(db)
    roles = repo.listar_todos()
    return [
        {
            "id": r.id,
            "nombre": r.nombre,
            "nivel": r.nivel,
            "permisos": r.permisos.split(",") if r.permisos else [],
        }
        for r in roles
    ]


@router.get("/{id_rol}")
def obtener_rol(id_rol: int, db: Session = Depends(get_db)):
    """Obtiene un rol por su ID."""
    repo = RolRepository(db)
    rol = repo.obtener_por_id(id_rol)
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")

    return {
        "id": rol.id,
        "nombre": rol.nombre,
        "nivel": rol.nivel,
        "permisos": rol.permisos.split(",") if rol.permisos else [],
    }