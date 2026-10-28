from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.database import get_db
from backend.usuarios.presentation.auth_routes import hash_password, administrador, constancia_path
from backend.usuarios.application.registrar_usuario import RegistrarUsuarioUseCase
from backend.usuarios.application.asignar_rol import AsignarRolUseCase
from backend.usuarios.application.gestionar_perfil import (
    GestionarPerfilUseCase,
    GestionarCredibilidadUseCase,
)
from backend.usuarios.infraestructure.usuario_repository import (
    UsuarioRepository,
    RolRepository,
)
from backend.shared.mailer import correo_aprobacion, correo_rechazo
from backend.usuarios.domain.usuario import EstadoUsuario
from backend.usuarios.infraestructure.models import UsuarioModel


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# ---------- Esquemas Pydantic ----------

class UsuarioCreate(BaseModel):
    nombre: str
    correo: str
    codigo: str
    password: str
    tipo: Literal['Estudiante', 'Profesor', 'Administrativo']
    carrera: str | None = None
    matricula: str | None = None
    departamento: str | None = None
    especialidad: str | None = None
    area: str | None = None
    cargo: str | None = None


class AsignarRolRequest(BaseModel):
    id_rol: int


class ActualizarPerfilRequest(BaseModel):
    nombre: str | None = None
    correo: str | None = None


class CambiarEstadoRequest(BaseModel):
    estado: str  # "ACTIVO" | "INACTIVO" | "SUSPENDIDO" | "PENDIENTE_APROBACION"


class AjustarCredibilidadRequest(BaseModel):
    delta: float
    motivo: str


class EstablecerCredibilidadRequest(BaseModel):
    valor: float
    motivo: str


class AprobarRequest(BaseModel):
    forzar: bool = False


class RechazarRequest(BaseModel):
    motivo: str = Field(min_length=10, max_length=500)


# ---------- FLUJO DE APROBACIÓN DE SOLICITUDES (Debe ir antes de /{id_usuario}) ----------

@router.get("/solicitudes")
def listar_solicitudes(db: Session = Depends(get_db)):
    """Lista todos los usuarios en estado PENDIENTE_APROBACION."""
    solicitudes = db.query(UsuarioModel).filter(
        UsuarioModel.estado == EstadoUsuario.PENDIENTE_APROBACION
    ).order_by(UsuarioModel.fecha_solicitud.asc()).all()

    return [
        {
            "id": u.id,
            "nombre": u.nombre,
            "correo": u.correo_institucional,
            "codigo": u.codigo_institucional,
            "tipo": u.tipo,
            "fecha_solicitud": u.fecha_solicitud.isoformat() if u.fecha_solicitud else None,
            "verificado_externo": u.verificado_externo,
            "constancia_matricula": u.tipo == "estudiante" and constancia_path(u.id).is_file(),
            "detalles": {
                "carrera": u.carrera,
                "departamento": u.departamento,
                "especialidad": u.especialidad,
                "area": u.area,
                "cargo": u.cargo,
            }
        }
        for u in solicitudes
    ]


@router.get("/solicitudes/count")
def contar_solicitudes(db: Session = Depends(get_db)):
    """Devuelve el total de solicitudes pendientes (para el badge del menú)."""
    total = db.query(UsuarioModel).filter(
        UsuarioModel.estado == EstadoUsuario.PENDIENTE_APROBACION
    ).count()
    return {"total": total}


@router.post("/{id_usuario}/aprobar")
def aprobar_usuario(id_usuario: int, request: AprobarRequest, db: Session = Depends(get_db),
                    admin=Depends(administrador)):
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == id_usuario).first()
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado.")
    if usuario.estado != EstadoUsuario.PENDIENTE_APROBACION:
        raise HTTPException(400, "Esta cuenta no está pendiente de aprobación.")
    if not usuario.verificado_externo and not request.forzar:
        raise HTTPException(400, "El sistema externo no verificó a este usuario. Usa 'forzar=true' si lo confirmaste manualmente.")

    usuario.estado = EstadoUsuario.ACTIVO
    usuario.revisado_por_id = admin.id
    usuario.fecha_revision = datetime.now(timezone.utc).replace(tzinfo=None)
    usuario.motivo_rechazo = None
    db.commit()
    db.refresh(usuario)

    correo_aprobacion(usuario.nombre, usuario.correo_institucional)
    return {"mensaje": f"Usuario {usuario.nombre} aprobado.", "id": usuario.id}


@router.post("/{id_usuario}/rechazar")
def rechazar_usuario(id_usuario: int, request: RechazarRequest, db: Session = Depends(get_db),
                     admin=Depends(administrador)):
    usuario = db.query(UsuarioModel).filter(UsuarioModel.id == id_usuario).first()
    if not usuario:
        raise HTTPException(404, "Usuario no encontrado.")
    if usuario.estado != EstadoUsuario.PENDIENTE_APROBACION:
        raise HTTPException(400, "Esta cuenta no está pendiente de aprobación.")

    usuario.estado = EstadoUsuario.INACTIVO
    usuario.motivo_rechazo = request.motivo.strip()
    usuario.revisado_por_id = admin.id
    usuario.fecha_revision = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    db.refresh(usuario)

    correo_rechazo(usuario.nombre, usuario.correo_institucional, usuario.motivo_rechazo)
    return {"mensaje": f"Solicitud de {usuario.nombre} rechazada.", "id": usuario.id}


# ---------- CRUD de Usuarios (Rutas con {id_usuario}) ----------

@router.post("/", status_code=201)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """RF01 - Crea un nuevo usuario desde el panel de administrador. El rol se asigna automáticamente según el tipo."""
    repo = UsuarioRepository(db)
    rol_repo = RolRepository(db)
    caso_uso = RegistrarUsuarioUseCase(repo, rol_repo)

    try:
        datos = usuario.model_dump(exclude={'password'})
        datos['password_hash'] = hash_password(usuario.password)
        resultado = caso_uso.ejecutar(datos)
        return {
            "mensaje": "Usuario creado exitosamente",
            "id": resultado.id,
            "nombre": resultado.nombre,
            "tipo": resultado.tipo,
            "rol_id": resultado.rol_id,
        }
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='El correo o código institucional ya está registrado.')
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
def listar_usuarios(
    tipo: str | None = Query(None, description="Filtrar por tipo: estudiante, profesor, administrativo"),
    estado: str | None = Query(None, description="Filtrar por estado: ACTIVO, INACTIVO, SUSPENDIDO, PENDIENTE_APROBACION"),
    db: Session = Depends(get_db),
):
    """RF20 - Lista todos los usuarios con filtros opcionales."""
    repo = UsuarioRepository(db)
    usuarios = repo.listar_todos()

    if tipo:
        usuarios = [u for u in usuarios if u.tipo == tipo.lower()]
    if estado:
        usuarios = [u for u in usuarios if u.estado and u.estado.value == estado.upper()]

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
            "constancia_matricula": u.tipo == "estudiante" and constancia_path(u.id).is_file(),
        }
        for u in usuarios
    ]


@router.get("/{id_usuario}")
def obtener_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """RF03 - Obtiene un usuario por su ID."""
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


@router.put("/{id_usuario}")
def actualizar_perfil(
    id_usuario: int,
    request: ActualizarPerfilRequest,
    db: Session = Depends(get_db),
):
    """RF03 - Actualiza el nombre y/o correo de un usuario."""
    repo = UsuarioRepository(db)
    caso_uso = GestionarPerfilUseCase(repo)

    try:
        usuario = caso_uso.actualizar_perfil(id_usuario, request.model_dump())
        return {
            "mensaje": "Perfil actualizado exitosamente",
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo_institucional,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id_usuario}/estado")
def cambiar_estado(
    id_usuario: int,
    request: CambiarEstadoRequest,
    db: Session = Depends(get_db),
):
    """RF03 - Cambia el estado del usuario: ACTIVO, INACTIVO o SUSPENDIDO."""
    repo = UsuarioRepository(db)
    caso_uso = GestionarPerfilUseCase(repo)

    try:
        usuario = caso_uso.cambiar_estado(id_usuario, request.estado)
        return {
            "mensaje": f"Estado cambiado a {request.estado}",
            "id": usuario.id,
            "estado": usuario.estado.value,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{id_usuario}")
def eliminar_usuario(id_usuario: int, db: Session = Depends(get_db)):
    """RF03/RF20 - Elimina un usuario del sistema."""
    repo = UsuarioRepository(db)
    caso_uso = GestionarPerfilUseCase(repo)

    try:
        resultado = caso_uso.eliminar_usuario(id_usuario)
        constancia_path(id_usuario).unlink(missing_ok=True)
        return {
            "mensaje": "Usuario eliminado exitosamente",
            **resultado,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{id_usuario}/rol")
def asignar_rol(id_usuario: int, request: AsignarRolRequest, db: Session = Depends(get_db)):
    """RF04 - Asigna un rol a un usuario existente."""
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


@router.put("/{id_usuario}/credibilidad/ajustar")
def ajustar_credibilidad(
    id_usuario: int,
    request: AjustarCredibilidadRequest,
    db: Session = Depends(get_db),
):
    """RF19 - Ajusta la credibilidad sumando o restando puntos."""
    repo = UsuarioRepository(db)
    caso_uso = GestionarCredibilidadUseCase(repo)

    try:
        usuario = caso_uso.ajustar_credibilidad(
            id_usuario, request.delta, request.motivo
        )
        return {
            "mensaje": "Credibilidad ajustada exitosamente",
            "id": usuario.id,
            "credibilidad": usuario.credibilidad,
            "motivo": request.motivo,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id_usuario}/credibilidad")
def establecer_credibilidad(
    id_usuario: int,
    request: EstablecerCredibilidadRequest,
    db: Session = Depends(get_db),
):
    """RF19 - Establece un valor específico de credibilidad (0-100)."""
    repo = UsuarioRepository(db)
    caso_uso = GestionarCredibilidadUseCase(repo)

    try:
        usuario = caso_uso.establecer_credibilidad(
            id_usuario, request.valor, request.motivo
        )
        return {
            "mensaje": "Credibilidad establecida exitosamente",
            "id": usuario.id,
            "credibilidad": usuario.credibilidad,
            "motivo": request.motivo,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))