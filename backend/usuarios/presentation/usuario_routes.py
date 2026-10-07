from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.usuarios.application.registrar_usuario import RegistrarUsuarioUseCase
from backend.usuarios.infraestructure.usuario_repository import UsuarioRepository

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Esquema de entrada (Pydantic) - Incluye campos de todos los tipos
class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    codigo: str
    tipo: str # "Estudiante", "Profesor", "Administrativo"
    
    # Campos opcionales según el tipo
    carrera: str | None = None
    matricula: str | None = None
    departamento: str | None = None
    especialidad: str | None = None
    area: str | None = None
    cargo: str | None = None

@router.post("/")
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    repo = UsuarioRepository(db)
    caso_uso = RegistrarUsuarioUseCase(repo)
    
    try:
        # Validar si ya existe el correo
        if repo.obtener_por_correo(usuario.correo):
            raise HTTPException(status_code=400, detail="El correo ya está registrado")

        resultado = caso_uso.ejecutar(usuario.dict())
        
        # Retornamos un diccionario simple (podrías usar un esquema de respuesta Pydantic)
        return {
            "mensaje": "Usuario creado exitosamente",
            "id": resultado.id,
            "nombre": resultado.nombre,
            "tipo": resultado.tipo
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))