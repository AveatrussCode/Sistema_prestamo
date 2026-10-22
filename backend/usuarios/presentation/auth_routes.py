"""Local accounts and expiring sessions for existing users."""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal
from sqlalchemy.exc import IntegrityError
from backend.usuarios.infraestructure.models import EstudianteModel, ProfesorModel, RolModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Session
from backend.database import Base, get_db
from backend.usuarios.infraestructure.models import UsuarioModel
from backend.usuarios.domain.usuario import EstadoUsuario

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

def hash_password(password: str) -> str:
    salt=secrets.token_hex(16)
    digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex()
    return f'{salt}${digest}'

def verificar(password: str, stored: str) -> bool:
    salt,digest=stored.split('$',1)
    actual=hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),600000).hex()
    return hmac.compare_digest(actual,digest)

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def usuario_actual(request: Request, db: Session = Depends(get_db)):
    token=request.cookies.get(COOKIE)
    session=db.get(SesionModel,token_hash(token)) if token else None
    if not session or session.expires_at <= datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(401,'Inicia sesion para continuar.')
    user=db.get(UsuarioModel,session.usuario_id)
    if not user or user.estado != EstadoUsuario.ACTIVO:
        raise HTTPException(401,'La cuenta no esta activa.')
    return user

def administrador(user=Depends(usuario_actual)):
    if not user.rol or user.rol.nombre != 'ADMIN':
        raise HTTPException(403,'Esta accion requiere una cuenta administrativa.')
    return user

def perfil(user):
    from backend.usuarios.presentation.matricula_routes import constancia_path
    datos = {'id':user.id,'nombre':user.nombre,'correo':user.correo_institucional,'tipo':user.tipo,'administrador':bool(user.rol and user.rol.nombre=='ADMIN')}
    datos.update(codigo=user.codigo_institucional, credibilidad=user.credibilidad, carrera=user.carrera, especialidad=user.especialidad, departamento=user.departamento, area=user.area, cargo=user.cargo, constancia_matricula=user.tipo=='estudiante' and constancia_path(user.id).is_file())
    return datos

class LoginRequest(BaseModel):
    correo: str
    password: str

@router.post('/login')
def login(datos: LoginRequest, response: Response, request: Request, db: Session=Depends(get_db)):
    user=db.query(UsuarioModel).filter(UsuarioModel.correo_institucional==datos.correo.strip().lower()).first()
    account=db.get(CuentaModel,user.id) if user else None
    if not account or not verificar(datos.password,account.password_hash) or user.estado != EstadoUsuario.ACTIVO:
        raise HTTPException(401,'Correo o contrasena incorrectos, o cuenta inactiva.')
    old=request.cookies.get(COOKIE)
    if old:
        existing=db.get(SesionModel,token_hash(old))
        if existing: db.delete(existing)
    token=secrets.token_urlsafe(32)
    db.add(SesionModel(token_hash=token_hash(token),usuario_id=user.id,expires_at=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(hours=8)))
    db.commit()
    response.set_cookie(COOKIE,token,httponly=True,samesite='lax',max_age=8*3600,path='/')
    return perfil(user)

@router.get('/me')
def me(user=Depends(usuario_actual)):
    return perfil(user)

@router.post('/logout')
def logout(request: Request,response: Response,db: Session=Depends(get_db)):
    token=request.cookies.get(COOKIE)
    session=db.get(SesionModel,token_hash(token)) if token else None
    if session:
        db.delete(session);db.commit()
    response.delete_cookie(COOKIE,path='/')
    return {'mensaje':'Sesion cerrada'}


class RegistroRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str = Field(min_length=2, max_length=150)
    correo: str = Field(min_length=5, max_length=200)
    codigo: str = Field(min_length=1, max_length=50)
    tipo: Literal['Estudiante', 'Profesor']
    password: str = Field(min_length=8, max_length=128)
    especialidad: str = Field(default="", max_length=150)

    @field_validator('nombre', 'correo', 'codigo', mode='before')
    @classmethod
    def limpiar(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator('correo')
    @classmethod
    def validar_correo(cls, value):
        import re
        value=value.lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Ingresa un correo valido.')
        return value

@router.post('/register', status_code=201)
def registrar(datos: RegistroRequest, db: Session=Depends(get_db)):
    if db.query(UsuarioModel).filter(UsuarioModel.correo_institucional==datos.correo).first():
        raise HTTPException(409, 'Este correo ya esta registrado. Inicia sesion con tu cuenta.')
    if db.query(UsuarioModel).filter(UsuarioModel.codigo_institucional==datos.codigo).first():
        raise HTTPException(409, 'Este codigo institucional ya esta registrado.')
    rol=db.query(RolModel).filter(RolModel.nombre=='USUARIO_BASICO').first()
    if not rol:
        raise HTTPException(503, 'No se pudo preparar la cuenta. Contacta al administrador.')
    modelo=EstudianteModel if datos.tipo=='Estudiante' else ProfesorModel
    user=modelo(nombre=datos.nombre,correo_institucional=datos.correo,codigo_institucional=datos.codigo,
                tipo=datos.tipo.lower(),estado=EstadoUsuario.ACTIVO,credibilidad=100,rol_id=rol.id)
    if datos.tipo=='Estudiante':
        user.carrera='Ciencia de la Computaci\u00f3n'
    else:
        user.departamento='Ciencia de la Computaci\u00f3n'
        user.especialidad=datos.especialidad.strip()
    try:
        db.add(user)
        db.flush()
        db.add(CuentaModel(usuario_id=user.id,password_hash=hash_password(datos.password)))
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'El correo o codigo institucional ya esta registrado.')
    return {'id':user.id,'mensaje':'Cuenta creada. Ya puedes iniciar sesion.'}


class PerfilRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nombre: str = Field(min_length=2, max_length=150)
    especialidad: str = Field(default='', max_length=150)

    @field_validator('nombre', mode='before')
    @classmethod
    def limpiar(cls, value):
        return value.strip() if isinstance(value, str) else value

@router.put('/me')
def actualizar_mi_perfil(datos: PerfilRequest, user=Depends(usuario_actual), db: Session=Depends(get_db)):
    user.nombre=datos.nombre
    if user.tipo=='profesor':
        user.especialidad=datos.especialidad.strip()
    db.commit()
    db.refresh(user)
    return perfil(user)
