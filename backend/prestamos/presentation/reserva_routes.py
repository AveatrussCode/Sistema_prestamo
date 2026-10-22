from backend.usuarios.presentation.auth_routes import usuario_actual, administrador
from datetime import date

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.prestamos.application.reserva_service import ReservaService
from backend.prestamos.domain.reserva import EstadoReserva, Reserva
from backend.prestamos.infraestructure.sql_reserva_repository import SqlReservaRepository
from backend.recursos.infraestructure.sql_objeto_repository import SqlObjetoRepository
from backend.usuarios.infraestructure.usuario_repository import UsuarioRepository

router = APIRouter(prefix="/reservas", tags=["Reservas"])


# ---------- 1) Esquema de entrada: qué JSON acepta el endpoint ----------

class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    usuario_id: int = Field(gt=0)
    objeto_id: int = Field(gt=0)
    fecha_inicio: date    # "2026-11-03"
    fecha_fin: date


# ---------- 2) Armado del servicio (inyección de dependencias) ----------

def get_reserva_service(db: Session = Depends(get_db)) -> ReservaService:
    return ReservaService(SqlReservaRepository(db), SqlObjetoRepository(db), UsuarioRepository(db))


# ---------- 3) Salida: entidad de dominio -> JSON ----------

def _a_dict(r: Reserva) -> dict:
    return {
        "id": r.id_reserva,
        "usuario_id": r.usuario_id,
        "objeto_id": r.objeto_id,
        "fecha_reserva": r.fecha_reserva.isoformat(),
        "fecha_inicio": r.fecha_inicio.isoformat(),
        "fecha_fin": r.fecha_fin.isoformat(),
        "estado": r.estado.value,
    }


# ---------- 4) Endpoints: delgados, solo traducen HTTP <-> servicio ----------

@router.post("/", status_code=201)
def crear_reserva(datos: ReservaCreate, actor=Depends(usuario_actual), servicio: ReservaService = Depends(get_reserva_service)):
    """RF17 - Reserva de objetos."""
    if not es_admin(actor) and datos.usuario_id != actor.id:
        raise HTTPException(403, "Solo puedes crear tus propias reservas.")
    return _a_dict(servicio.crear(datos.usuario_id, datos.objeto_id,
                                  datos.fecha_inicio, datos.fecha_fin))


@router.get("/")
def listar_reservas(
    actor=Depends(usuario_actual),
    usuario_id: int | None = Query(None),
    objeto_id: int | None = Query(None),
    estado: EstadoReserva | None = Query(None),
    servicio: ReservaService = Depends(get_reserva_service),
):
    """RF18 - Consulta de reservas (con filtros opcionales)."""
    if not es_admin(actor):
        usuario_id = actor.id
    return [_a_dict(r) for r in servicio.listar(usuario_id, objeto_id, estado)]


@router.post("/procesar-vencidas", dependencies=[Depends(administrador)])
def procesar_vencidas(servicio: ReservaService = Depends(get_reserva_service)):
    """Marca como VENCIDAS las reservas activas cuya fecha de fin ya pasó."""
    return [_a_dict(r) for r in servicio.marcar_vencidas()]


@router.get("/{id_reserva}")
def obtener_reserva(id_reserva: int, actor=Depends(usuario_actual), servicio: ReservaService = Depends(get_reserva_service)):
    comprobar_acceso(actor, servicio.obtener(id_reserva))
    return _a_dict(servicio.obtener(id_reserva))


@router.post("/{id_reserva}/confirmar", dependencies=[Depends(administrador)])
def confirmar_reserva(id_reserva: int, servicio: ReservaService = Depends(get_reserva_service)):
    return _a_dict(servicio.confirmar(id_reserva))


@router.post("/{id_reserva}/cancelar")
def cancelar_reserva(id_reserva: int, actor=Depends(usuario_actual), servicio: ReservaService = Depends(get_reserva_service)):
    """RF18 - Cancelación de reservas."""
    comprobar_acceso(actor, servicio.obtener(id_reserva))
    return _a_dict(servicio.cancelar(id_reserva))


@router.post("/{id_reserva}/finalizar", dependencies=[Depends(administrador)])
def finalizar_reserva(id_reserva: int, servicio: ReservaService = Depends(get_reserva_service)):
    return _a_dict(servicio.finalizar(id_reserva))


def es_admin(actor):
    return bool(actor.rol and actor.rol.nombre == 'ADMIN')

def comprobar_acceso(actor, reserva):
    if not es_admin(actor) and reserva.usuario_id != actor.id:
        raise HTTPException(403, 'No puedes acceder a la reserva de otro usuario.')
