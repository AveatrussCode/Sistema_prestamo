"""Cuentas locales, sesiones y registro con aprobación."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, File, Form
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Session
from backend.database import Base, get_db
from backend.usuarios.infraestructure.models import (
    UsuarioModel, EstudianteModel, ProfesorModel, AdministrativoModel, RolModel
)
from backend.usuarios.domain.usuario import EstadoUsuario
from backend.usuarios.application.validar_institucional import validador_institucional
from backend.shared.mailer import (
    correo_solicitud_recibida, correo_aprobacion, correo_rechazo
)
import os
from pathlib import Path


# ---- Modelos de cuenta y sesión (los mismos de antes) ----
class CuentaModel(Base):
    __tablename__ = 'cuentas'
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), primary_key=True)
    password_hash = Column(String, nullable=False)


class SesionModel(Base):
    __tablename__ = 'sesiones'
    token_hash = Column(String, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)


router = APIRouter(prefix='/auth', tags=['Autenticacion'])
COOKIE = 'epcc_session'

# ---- Directorio de constancias ----
UPLOAD_DIR = Path(os.environ.get('MATRICULAS_DIR',
                                 str(Path(__file__).resolve().parents[3] / 'uploads' / 'matriculas')))
MAX_BYTES = 5 * 1024 * 1024


def constancia_path(usuario_id: int) -> Path:
    return UPLOAD_DIR / f'{usuario_id}.pdf'


def guardar_pdf(usuario_id: int, contenido: bytes):
    """Valida y guarda el PDF. Lanza HTTPException si es inválido."""
    if not contenido:
        raise HTTPException(422, 'La constancia de matrícula es obligatoria.')
    if len(contenido) > MAX_BYTES:
        raise HTTPException(413, 'El PDF no debe superar los 5 MB.')
    if not contenido.startswith(b'%PDF-') or b'%%EOF' not in contenido[-1024:]:
        raise HTTPException(400, 'El archivo no tiene un formato PDF válido.')
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    constancia_path(usuario_id).write_bytes(contenido)


# ---- Seguridad de contraseñas ----
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return f'{salt}${digest}'


def verificar(password: str, stored: str) -> bool:
    salt, digest = stored.split('$', 1)
    actual = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000).hex()
    return hmac.compare_digest(actual, digest)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ---- Dependencias ----
def usuario_actual(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    session = db.get(SesionModel, token_hash(token)) if token else None
    if not session or session.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(401, 'Inicia sesion para continuar.')
    user = db.get(UsuarioModel, session.usuario_id)
    if not user:
        raise HTTPException(401, 'La cuenta no existe.')
    if user.estado == EstadoUsuario.PENDIENTE_APROBACION:
        raise HTTPException(403, 'Tu solicitud está en revisión. Te avisaremos por correo.')
    if user.estado != EstadoUsuario.ACTIVO:
        raise HTTPException(401, 'La cuenta no esta activa.')
    return user


def administrador(user=Depends(usuario_actual)):
    if not user.rol or user.rol.nombre != 'ADMIN':
        raise HTTPException(403, 'Esta accion requiere una cuenta administrativa.')
    return user


def perfil(user):
    datos = {
        'id': user.id, 'nombre': user.nombre, 'correo': user.correo_institucional,
        'tipo': user.tipo,
        'administrador': bool(user.rol and user.rol.nombre == 'ADMIN')
    }
    datos.update(
        codigo=user.codigo_institucional, credibilidad=user.credibilidad,
        carrera=user.carrera, especialidad=user.especialidad,
        departamento=user.departamento, area=user.area, cargo=user.cargo,
        constancia_matricula=user.tipo == 'estudiante' and constancia_path(user.id).is_file()
    )
    return datos


# ---- Login / logout / me ----
class LoginRequest(BaseModel):
    correo: str
    password: str


@router.post('/login')
def login(datos: LoginRequest, response: Response, request: Request, db: Session = Depends(get_db)):
    user = db.query(UsuarioModel).filter(
        UsuarioModel.correo_institucional == datos.correo.strip().lower()
    ).first()
    account = db.get(CuentaModel, user.id) if user else None
    if not account or not verificar(datos.password, account.password_hash):
        raise HTTPException(401, 'Correo o contraseña incorrectos.')
    # Mensajes específicos según estado
    if user.estado == EstadoUsuario.PENDIENTE_APROBACION:
        raise HTTPException(403, 'Tu solicitud está en revisión. Te avisaremos por correo cuando sea aprobada.')
    if user.estado == EstadoUsuario.INACTIVO and user.motivo_rechazo:
        raise HTTPException(403, f'Tu solicitud fue rechazada: {user.motivo_rechazo}')
    if user.estado == EstadoUsuario.SUSPENDIDO:
        raise HTTPException(403, 'Tu cuenta está suspendida. Contacta al administrador.')
    if user.estado != EstadoUsuario.ACTIVO:
        raise HTTPException(401, 'La cuenta no esta activa.')

    old = request.cookies.get(COOKIE)
    if old:
        existing = db.get(SesionModel, token_hash(old))
        if existing:
            db.delete(existing)
    token = secrets.token_urlsafe(32)
    db.add(SesionModel(
        token_hash=token_hash(token), usuario_id=user.id,
        expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=8)
    ))
    db.commit()
    response.set_cookie(COOKIE, token, httponly=True, samesite='lax', max_age=8 * 3600, path='/')
    return perfil(user)


@router.get('/me')
def me(user=Depends(usuario_actual)):
    return perfil(user)


@router.post('/logout')
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(COOKIE)
    session = db.get(SesionModel, token_hash(token)) if token else None
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie(COOKIE, path='/')
    return {'mensaje': 'Sesion cerrada'}


# ---- Registro público (multipart/form-data) ----
@router.post('/register', status_code=201)
async def registrar(
    nombre: str = Form(...),
    correo: str = Form(...),
    codigo: str = Form(...),
    tipo: Literal['Estudiante', 'Profesor', 'Administrativo'] = Form(...),
    password: str = Form(...),
    especialidad: str = Form(default=""),
    area: str = Form(default=""),
    cargo: str = Form(default=""),
    constancia: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    nombre = nombre.strip()
    correo = correo.strip().lower()
    codigo = codigo.strip()

    # Validaciones básicas
    if len(nombre) < 2:
        raise HTTPException(422, 'El nombre debe tener al menos 2 caracteres.')
    if len(password) < 8:
        raise HTTPException(422, 'La contraseña debe tener al menos 8 caracteres.')
    import re
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', correo):
        raise HTTPException(422, 'Ingresa un correo válido.')

    # Duplicados
    if db.query(UsuarioModel).filter(UsuarioModel.correo_institucional == correo).first():
        raise HTTPException(409, 'Este correo ya está registrado. Inicia sesión con tu cuenta.')
    if db.query(UsuarioModel).filter(UsuarioModel.codigo_institucional == codigo).first():
        raise HTTPException(409, 'Este código institucional ya está registrado.')

    # Validación externa (profesores / administrativos)
    valido, motivo = validador_institucional.verificar(tipo, correo, codigo)

    # PDF obligatorio solo para estudiante
    pdf_bytes = await constancia.read() if constancia else None
    if tipo == 'Estudiante' and not pdf_bytes:
        raise HTTPException(422, 'La constancia de matrícula (PDF) es obligatoria.')

    rol_basico = db.query(RolModel).filter(RolModel.nombre == 'USUARIO_BASICO').first()
    if not rol_basico:
        raise HTTPException(503, 'No se pudo preparar la cuenta. Contacta al administrador.')

    # Crear el modelo según el tipo
    if tipo == 'Estudiante':
        user = EstudianteModel(
            nombre=nombre, correo_institucional=correo, codigo_institucional=codigo,
            tipo='estudiante', estado=EstadoUsuario.PENDIENTE_APROBACION,
            credibilidad=100, rol_id=rol_basico.id,
            carrera='Ciencia de la Computación', matricula='',
            fecha_solicitud=datetime.now(timezone.utc).replace(tzinfo=None),
            verificado_externo=valido,
        )
    elif tipo == 'Profesor':
        user = ProfesorModel(
            nombre=nombre, correo_institucional=correo, codigo_institucional=codigo,
            tipo='profesor', estado=EstadoUsuario.PENDIENTE_APROBACION,
            credibilidad=100, rol_id=rol_basico.id,
            departamento='Ciencia de la Computación', especialidad=especialidad.strip(),
            fecha_solicitud=datetime.now(timezone.utc).replace(tzinfo=None),
            verificado_externo=valido,
        )
    else:  # Administrativo
        if not area.strip() or not cargo.strip():
            raise HTTPException(422, 'Área y cargo son obligatorios para administrativos.')
        user = AdministrativoModel(
            nombre=nombre, correo_institucional=correo, codigo_institucional=codigo,
            tipo='administrativo', estado=EstadoUsuario.PENDIENTE_APROBACION,
            credibilidad=100, rol_id=rol_basico.id,
            departamento='Ciencia de la Computación',
            area=area.strip(), cargo=cargo.strip(),
            fecha_solicitud=datetime.now(timezone.utc).replace(tzinfo=None),
            verificado_externo=valido,
        )

    try:
        db.add(user)
        db.flush()  # obtiene el ID antes del commit
        db.add(CuentaModel(usuario_id=user.id, password_hash=hash_password(password)))
        if pdf_bytes:
            guardar_pdf(user.id, pdf_bytes)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'El correo o código institucional ya está registrado.')
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f'Error al crear la cuenta: {e}')

    # Notificar por correo (modo consola por defecto)
    correo_solicitud_recibida(nombre, correo, tipo)

    return {
        'id': user.id,
        'mensaje': 'Solicitud recibida. Un administrador la revisará pronto.',
        'verificado_externo': valido,
        'advertencia': motivo if not valido else '',
    }


# ---- Perfil propio ----
class PerfilRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str = Field(min_length=2, max_length=150)
    especialidad: str = Field(default='', max_length=150)

    @field_validator('nombre', mode='before')
    @classmethod
    def limpiar(cls, value):
        return value.strip() if isinstance(value, str) else value

class CambiarPasswordRequest(BaseModel):
    password_actual: str = Field(min_length=1)
    password_nueva: str = Field(min_length=8, max_length=128)

@router.put('/me')
def actualizar_mi_perfil(datos: PerfilRequest, user=Depends(usuario_actual), db: Session = Depends(get_db)):
    user.nombre = datos.nombre
    if user.tipo == 'profesor':
        user.especialidad = datos.especialidad.strip()
    db.commit()
    db.refresh(user)
    return perfil(user)

@router.put('/me/password')
def cambiar_mi_password(datos: CambiarPasswordRequest, user=Depends(usuario_actual), db: Session = Depends(get_db)):
    """Permite al usuario autenticado cambiar su propia contraseña."""
    cuenta = db.get(CuentaModel, user.id)
    if not cuenta:
        raise HTTPException(404, 'No se encontró la cuenta de usuario.')
        
    # Verificar que la contraseña actual sea correcta
    if not verificar(datos.password_actual, cuenta.password_hash):
        raise HTTPException(401, 'La contraseña actual es incorrecta.')
        
    # Actualizar con la nueva contraseña encriptada
    cuenta.password_hash = hash_password(datos.password_nueva)
    db.commit()
    
    return {'mensaje': 'Contraseña actualizada correctamente.'}