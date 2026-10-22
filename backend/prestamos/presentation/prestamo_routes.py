from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.prestamos.application.prestamo_service import PrestamoService, prestamo_dict
from backend.usuarios.presentation.auth_routes import usuario_actual, administrador
from backend.recursos.domain.enums import EstadoFisico

router = APIRouter(prefix='/prestamos', tags=['Préstamos'])


class EntregaCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    reserva_id: int = Field(gt=0)
    observaciones: str = Field(default='', max_length=2000)


class DevolucionCreate(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    estado_fisico: EstadoFisico
    observaciones: str = Field(default='', max_length=2000)


@router.post('/', status_code=201)
def entregar(datos: EntregaCreate, actor=Depends(administrador), db: Session = Depends(get_db)):
    return prestamo_dict(PrestamoService(db).entregar(datos.reserva_id, actor.id, datos.observaciones))


@router.post('/{prestamo_id}/devolucion', status_code=201)
def devolver(prestamo_id: int, datos: DevolucionCreate, actor=Depends(administrador), db: Session = Depends(get_db)):
    return prestamo_dict(PrestamoService(db).devolver(prestamo_id, actor.id, datos.estado_fisico, datos.observaciones))


@router.get('/')
def listar(actor=Depends(usuario_actual), db: Session = Depends(get_db)):
    admin = bool(actor.rol and actor.rol.nombre == 'ADMIN')
    return [prestamo_dict(p) for p in PrestamoService(db).listar(None if admin else actor.id)]
