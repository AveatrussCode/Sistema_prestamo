from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.usuarios.application.registrar_usuario import RegistrarUsuarioUseCase
from backend.usuarios.application.asignar_rol import AsignarRolUseCase
from backend.usuarios.infraestructure.usuario_repository import UsuarioRepository, RolRepository


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ---------- Esquemas Pydantic ----------

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    codigo: str
    tipo: str  # "Estudiante" | "Profesor" | "Administrativo"
    carrera: str | None = None
    matricula: str | None = None
    departamento: str | None = None
    especialidad: str | None = None
    area: str | None = None
    cargo: str | None = None


class AsignarRolRequest(BaseModel):
    id_rol: int


# ---------- Endpoints ----------

@router.post("/", status_code=201)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Crea un nuevo usuario. El rol se asigna automáticamente según el tipo."""
    repo = UsuarioRepository(db)
    rol_repo = RolRepository(db)
    caso_uso = RegistrarUsuarioUseCase(repo, rol_repo)

    try:
        resultado = caso_uso.ejecutar(usuario.model_dump())
        return {
            "mensaje": "Usuario creado exitosamente",
            "id": resultado.id,
            "nombre": resultado.nombre,
            "tipo": resultado.tipo,
            "rol_id": resultado.rol_id,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def listar_usuarios(db: Session = Depends(get_db)):
    """Lista todos los usuarios del sistema."""
    repo = UsuarioRepository(db)
    usuarios = repo.listar_todos()
    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "correo": u.correo_institucional,
            "codigo": u.codigo_institucional,
            "tipo": u.tipo,
            "estado": u.estado.value if u.estado else None,
            "credibilidad": u.credibilidad,
            "rol": u.rol.nombre if u.rol else None,
        }
        for u in usuarios
    ]


@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """Obtiene un usuario por su ID."""
    repo = UsuarioRepository(db)
    usuario = repo.obtener_por_id(id_usuario)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo_institucional,
        "codigo": usuario.codigo_institucional,
        "tipo": usuario.tipo,
        "estado": usuario.estado.value if usuario.estado else None,
        "credibilidad": usuario.credibilidad,
        "rol": usuario.rol.nombre if usuario.rol else None,
        "detalles": {
            "carrera": usuario.carrera,
            "matricula": usuario.matricula,
            "departamento": usuario.departamento,
            "especialidad": usuario.especialidad,
            "area": usuario.area,
            "cargo": usuario.cargo,
        }
    }


@router.put("/{id_usuario}/rol")
def asignar_rol(id_usuario: int, request: AsignarRolRequest, db: Session = Depends(get_db)):
    """Asigna un rol a un usuario existente."""
    repo = UsuarioRepository(db)
    caso_uso = AsignarRolUseCase(repo)

    try:
        usuario = caso_uso.ejecutar(id_usuario, request.id_rol)
        return {
            "mensaje": "Rol asignado exitosamente",
            "id_usuario": usuario.id,
            "rol_id": usuario.rol_id,
            "rol": usuario.rol.nombre if usuario.rol else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))